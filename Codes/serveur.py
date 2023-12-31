import datetime
import threading
import socket
import pymysql
import json
import time
import sys


class ServeurDeMessagerie:

    def __init__(self, hote, port, mysql):
        """
        Constructeur de la classe ServeurDeMessagerie.

        :param hote: L'adresse IP  du serveur.
        :param port: Le port sur lequel le serveur écoutera les connexions.
        :param mysql: Les informations de configuration pour la BDD MySQL.
        """

        self.hote = hote
        self.port = port
        self.mysql = mysql
        self.clients = {}
        self.sessions = {}
        self.lien_mysql = None
        self.requete_acces_en_cours = False
        self.verrou_requete_acces = threading.Lock()
        self.arret_serveur = False
        self.etat_commande = "commande"

    def connexion_mysql(self):
        """
        Établit une connexion à la base de données MySQL en utilisant
        les informations de configuration.
        """

        try:

            self.lien_mysql = pymysql.connect(**self.mysql)
            print("Connexion à la BDD réussie.")

        except Exception as erreur:

            print(f"Erreur de connexion à la BDD: {erreur}")
            self.lien_mysql = None

    def demarrage_serveur(self):
        """
        Démarrage du serveur de messagerie.

        Cette méthode configure et démarre le serveur comme cela :
        1. Tente de se connecter à la base de données MySQL.
        2. Vérifie si la connexion à la base de données a réussi.
        3. Crée un socket pour écouter les connexions entrantes.
        4. Démarre un thread pour l'authentification de l'administrateur.
        5. Boucle principale pour gérer les connexions entrantes des clients.
        6. Finalement, fermeture propre de toutes les connexions.
        """
        
        self.connexion_mysql()

        if not self.lien_mysql:

            print("Impossible de démarrer le serveur sans connexion à la BDD.")
            return

        socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_serveur.bind((self.hote, self.port))
        socket_serveur.listen()
        print(f"Serveur lancé sur l'hôte {self.hote}, port {self.port}.\n")

        # Configuration du thread d'authentification administrateur
        thread_authentification_admin = threading.Thread(
            target=self.authentification_administrateur)
        thread_authentification_admin.start()

        try:

            while not self.arret_serveur:

                socket_serveur.settimeout(1)

                try:
                    socket_client, adresse_client = socket_serveur.accept()

                except socket.timeout:

                    continue

                thread_client = threading.Thread(
                    target=self.gestion_clients,
                    args=(socket_client, adresse_client))
                thread_client.start()

        except KeyboardInterrupt:

            print("Arrêt du serveur...")

        finally:

            self.fermeture_connexions_clients()
            socket_serveur.close()

    def authentification_client(self, email, mot_de_passe):
        """
        Cette méthode tente d'authentifier un client en vérifiant
        son email et son mot de passe dans la base de données.

        :param email: L'adresse e-mail du client.
        :param mot_de_passe: Le mot de passe du client.

        :return: Un tuple contenant l'ID du client et ses permissions
        s'il est authentifié, sinon (None, None).
        """

        try:

            connexion = self.lien_mysql.cursor()

            connexion.execute(
                "SELECT id_client, mot_de_passe, permission "
                "FROM clients WHERE email = %s", (email,))
            resultat = connexion.fetchone()

            if resultat and resultat[1] == mot_de_passe:

                id_client, _, permission = resultat
                connexion.close()
                return id_client, permission

            connexion.close()
            return None, None

        except Exception as erreur:

            print(f"\nErreur lors de l'authentification : {erreur}")
            return None, None

    def inscription_client(self, nom, prenom, email, mot_de_passe, permission):
        """
        Cette méthode tente d'inscrire un nouveau client
        en vérifiant d'abord si l'email est déjà utilisé.

        Si l'email n'est pas déjà enregistré, elle insère
        le nouveau client dans la base de données.

        :param nom: Le nom du client.
        :param prenom: Le prénom du client.
        :param email: L'adresse e-mail du client.
        :param mot_de_passe: Le mot de passe du client.
        :param permission: Les permissions du client.

        :return: "SUCCES_INSCRIPTION" en cas de succès,
        sinon un message d'échec.
        """

        try:

            connexion = self.lien_mysql.cursor()

            # Vérification si l'email est déjà utilisé
            connexion.execute("SELECT COUNT(*) FROM clients WHERE email = %s",
                              (email,))
            (nombre,) = connexion.fetchone()

            if nombre > 0:

                connexion.close()
                return "ECHEC_INSCRIPTION"

            # Insertion du nouveau client
            connexion.execute("INSERT INTO clients "
                              "(nom, prenom, email, mot_de_passe, permission) "
                              "VALUES (%s, %s, %s, %s, %s)",
                              (nom, prenom, email, mot_de_passe, permission))
            self.lien_mysql.commit()

            # Récupération de l'ID du client nouvellement inscrit
            connexion.execute("SELECT LAST_INSERT_ID()")
            (id_client,) = connexion.fetchone()

            # Récupération de l'ID du salon "General"
            connexion.execute(
                "SELECT id_salon_public "
                "FROM salons_publics WHERE nom_salon = 'General'")
            (id_salon_general,) = connexion.fetchone()

            # Vérification si le salon "General" existe
            if id_salon_general is None:

                print("\nErreur: Salon 'General' introuvable.")
                return "ECHEC_INSCRIPTION : Salon 'General' introuvable."

            # Ajout du client au salon "General"
            connexion.execute(
                "INSERT INTO membres_salons_publics "
                "(id_client, id_salon_public) VALUES (%s, %s)",
                (id_client, id_salon_general))
            self.lien_mysql.commit()

            connexion.close()
            return "SUCCES_INSCRIPTION"

        except Exception as erreur:

            print(f"\nErreur lors de l'inscription : {erreur}")
            return "ECHEC_INSCRIPTION : Erreur serveur."

    def ban_client(self, email_client, motif):
        """
        Bannir un client en enregistrant une sanction dans la base de données.

        Cette méthode enregistre une sanction de type "ban"
        pour un client spécifié, avec un motif par défaut.

        :param email_client: L'adresse e-mail du client à bannir.
        :param motif: Le motif du bannissement.
        """

        with self.lien_mysql.cursor() as curseur:

            curseur.execute("SELECT COUNT(*) FROM clients WHERE email = %s",
                            (email_client,))
            result = curseur.fetchone()

            if result[0] > 0:

                curseur.execute("""
                    INSERT INTO sanctions 
                    (type_sanction, motif_sanction, email_client, ip_client)
                    VALUES ('ban', %s, %s, 
                    (SELECT ip_client FROM historique_ip 
                    WHERE email_client = %s))
                """, (motif, email_client, email_client))

                self.lien_mysql.commit()
                print(f"\n{email_client} a été banni.")

                self.deconnecter_clients_par_email(email_client)

            else:

                print(f"\nAucun client existant pour l'email {email_client} !")

    def unban_client(self, email_client):
        """
        Révoquer le bannissement d'un client en supprimant
        les sanctions de type "ban" dans la base de données.

        :param email_client: L'adresse e-mail du client
        dont le bannissement doit être révoqué.
        """

        with self.lien_mysql.cursor() as curseur:

            curseur.execute("""
            SELECT COUNT(*) FROM sanctions
             WHERE type_sanction = 'ban' AND email_client = %s
             """, (email_client,))
            resultat = curseur.fetchone()

            if resultat[0] > 0:

                curseur.execute("""
                DELETE FROM sanctions 
                WHERE type_sanction = 'ban' AND email_client = %s
                """, (email_client,))
                self.lien_mysql.commit()
                print(f"\n{email_client} a été débanni.")

            else:

                print(f"\nAucune sanction BAN existante pour l'email "
                      f"{email_client}")

    def kick_client(self, email_client, duree, motif="Kick administratif."):
        """
        Cette méthode enregistre une sanction de type "kick" pour un client
        spécifié, en incluant la durée et le motif de l'exclusion.

        :param email_client: Adresse e-mail du client à exclure temporairement.
        :param duree: La durée de l'exclusion temporaire en minutes.
        :param motif: Le motif de l'exclusion.
        """

        with self.lien_mysql.cursor() as curseur:

            curseur.execute("""
            SELECT COUNT(*) FROM clients WHERE email = %s
            """, (email_client,))
            result = curseur.fetchone()

            if result[0] > 0:

                curseur.execute("""
                INSERT INTO sanctions 
                (type_sanction, duree_sanction, motif_sanction, 
                email_client, ip_client)
                VALUES ('kick', %s, %s, %s, 
                (SELECT ip_client FROM historique_ip WHERE email_client = %s))
                """, (duree, motif, email_client, email_client))
                self.lien_mysql.commit()

                print(f"\n{email_client} a été exclu temporairement pour "
                      f"{duree} minutes.")

                self.deconnecter_clients_par_email(email_client)

            else:

                print(f"\nAucun client existant pour l'email {email_client} !")

    def unkick_client(self, email_client):
        """
        Révoquer l'exclusion temporaire d'un client en supprimant
        les sanctions de type "kick" dans la base de données.

        :param email_client: L'adresse e-mail du client dont
        l'exclusion temporaire doit être révoquée.
        """

        with self.lien_mysql.cursor() as curseur:

            curseur.execute("""
            SELECT COUNT(*) FROM sanctions 
            WHERE type_sanction = 'kick' AND email_client = %s
            """, (email_client,))
            resultat = curseur.fetchone()

            if resultat[0] > 0:

                curseur.execute("""
                DELETE FROM sanctions 
                WHERE type_sanction = 'kick' AND email_client = %s
                """, (email_client,))
                self.lien_mysql.commit()
                print(f"\nLe kick sur {email_client} a été révoqué.")

            else:

                print(f"\nAucune sanction KICK existante pour l'email "
                      f"{email_client}.")

    def grant_access(self, nom_salon, email_client):
        """
        Ajoute un client en tant que membre d'un salon public spécifié.

        Cette méthode vérifie d'abord l'existence du salon et du client
        avant de l'ajouter comme membre du salon.

        :param nom_salon: Le nom du salon public.
        :param email_client: L'adresse e-mail du client à ajouter au salon.
        """

        with self.lien_mysql.cursor() as curseur:

            curseur.execute("""
            SELECT id_salon_public FROM salons_publics WHERE nom_salon = %s
            """, (nom_salon,))
            salon = curseur.fetchone()

            curseur.execute("""
            SELECT id_client FROM clients WHERE email = %s
            """, (email_client,))
            client = curseur.fetchone()

            if salon and client:

                curseur.execute("""
                SELECT COUNT(*) FROM membres_salons_publics 
                WHERE id_client = %s AND id_salon_public = %s
                """, (client[0], salon[0]))
                est_membre = curseur.fetchone()[0]

                if est_membre == 0:

                    curseur.execute("""
                    INSERT INTO 
                    membres_salons_publics (id_client, id_salon_public) 
                    VALUES (%s, %s)
                    """, (client[0], salon[0]))
                    self.lien_mysql.commit()

                    print(f"\n{email_client} a été ajouté au salon "
                          f"{nom_salon}.")

                else:

                    print(
                        f"\n{email_client} est déjà membre de {nom_salon}.")

            else:

                print("\nSalon ou client introuvable.")

    def revoke_access(self, nom_salon, email_client):
        """
        Retire un client d'un salon public spécifié.

        Cette méthode vérifie d'abord si le client est membre du salon
        avant de le retirer.

        :param nom_salon: Le nom du salon public.
        :param email_client: L'adresse e-mail du client à retirer du salon.
        """

        with self.lien_mysql.cursor() as curseur:

            curseur.execute("""
            SELECT id_salon_public FROM salons_publics WHERE nom_salon = %s
            """, (nom_salon,))
            salon = curseur.fetchone()

            curseur.execute("""
            SELECT id_client FROM clients WHERE email = %s
            """, (email_client,))
            client = curseur.fetchone()

            if salon and client:

                curseur.execute("""
                SELECT COUNT(*) FROM membres_salons_publics 
                WHERE id_client = %s AND id_salon_public = %s
                """, (client[0], salon[0]))
                est_membre = curseur.fetchone()[0]

                if est_membre > 0:

                    curseur.execute("""
                    DELETE FROM membres_salons_publics 
                    WHERE id_client = %s AND id_salon_public = %s
                    """, (client[0], salon[0]))
                    self.lien_mysql.commit()
                    print(f"\n{email_client} a été retiré du salon "
                          f"{nom_salon}.")

                else:

                    print(
                        f"\n{email_client} n'est pas déjà membre "
                        f"du salon {nom_salon}.")

            else:

                print("\nSalon ou client introuvable.")

    def verification_sanctions(self, email_client):
        """
        Vérifie les sanctions actives pour un client spécifié.

        :param email_client: L'adresse e-mail du client.
        :return: "BAN" si le client est banni, "KICK" si le client est kické,
                 "NONE" si aucune sanction active.
        """

        with self.lien_mysql.cursor() as curseur:

            curseur.execute("""
            SELECT COUNT(*) FROM sanctions 
            WHERE type_sanction = 'ban' AND email_client = %s
            """, (email_client,))

            if curseur.fetchone()[0] > 0:

                return "BAN"

            curseur.execute("""
            SELECT duree_sanction, 
            TIMESTAMPDIFF(MINUTE, horodatage_sanction, NOW()) 
            AS temps_ecoule
            FROM sanctions 
            WHERE type_sanction = 'kick' AND email_client = %s
            """, (email_client,))

            for ligne in curseur.fetchall():

                duree_sanction, temps_ecoule = ligne

                if temps_ecoule < duree_sanction:

                    return "KICK"

            return "NONE"

    def deconnecter_clients_par_email(self, email_client):

        with self.lien_mysql.cursor() as curseur:

            curseur.execute("""
            SELECT DISTINCT ip_client FROM historique_ip 
            WHERE email_client = %s
            """, (email_client,))

            ips_a_deconnecter = [ligne[0] for ligne in curseur.fetchall()]

            for ip in ips_a_deconnecter:

                if ip in self.clients:

                    try:

                        self.clients[ip].close()

                    except Exception as erreur:

                        print(f"\nErreur lors de la fermeture de la connexion "
                              f"pour l'IP {ip}: {erreur}")

                    finally:

                        del self.clients[ip]
                        del self.sessions[ip]

                        print(f"\nClient déconnecté suite à un ban/kick : "
                              f"{ip}")

    def authentification_administrateur(self):
        """
        Authentification de l'administrateur.

        Cette méthode permet à l'administrateur de s'authentifier
        en saisissant son email et son mot de passe.

        Si l'authentification réussit et que l'administrateur a les
        permissions nécessaires, elle démarre un thread pour gérer
        les commandes administratives.
        """

        while True:

            email_admin = input("Email Administrateur: ")
            motdepasse_admin = input("Mot de passe: ")
            id_client, permission = self.authentification_client(
                email_admin, motdepasse_admin)

            if id_client is not None and permission == "administrateur":

                print("Authentification réussie.\n")
                thread_admin = threading.Thread(
                    target=self.gestion_commandes_admin)
                thread_admin.start()
                break

            else:
                print("Échec de l'authentification.")

    def gestion_commandes_admin(self):
        """
        Cette méthode permet à l'administrateur d'entrer 
        des commandes spécifiques pour gérer le serveur.
        Elle peut effectuer des actions telles que l'arrêt du serveur, 
        le bannissement, le kick de clients ou encore l'octroi/la révocation
        d'accès à des salons.
        """
        
        while True:

            if self.etat_commande == "commande":

                commande = input("[ADMIN] Entrez une commande : ")

                if commande == "/kill":
                    
                    print("\nArrêt du serveur en cours...")
                    self.envoi_message_clients("[PROTOCOLE]ARRET_SERVEUR:")
                    time.sleep(5)
                    self.fermeture_connexions_clients()
                    self.arret_serveur = True
                    sys.exit(0)

                elif commande.startswith("/ban "):
                    
                    _, email_client = commande.split(" ", 1)
                    self.ban_client(email_client, "Ban administratif.")

                elif commande.startswith("/unban "):
                    
                    _, email_client = commande.split(" ", 1)
                    self.unban_client(email_client)

                elif commande.startswith("/kick "):

                    try:
                        _, email_client, duree = commande.split(" ", 3)
                        self.kick_client(email_client, int(duree),
                                         "Kick administratif.")

                    except ValueError:

                        print("\nProblème de syntaxe.")
                        continue

                elif commande.startswith("/unkick "):

                    _, email_client = commande.split(" ", 1)
                    self.unkick_client(email_client)

                elif commande.startswith("/grant "):
                    try:
                        _, nom_salon, email_client = commande.split(" ", 3)
                        self.grant_access(nom_salon, email_client)

                    except ValueError:

                        print("\nProblème de syntaxe.")

                elif commande.startswith("/revoke "):

                    try:
                        _, nom_salon, email_client = commande.split(" ", 3)
                        self.revoke_access(nom_salon, email_client)

                    except ValueError:

                        print("\nProblème de syntaxe.")

                else:
                    
                    print(f"\nCommande non reconnue : {commande}")

            elif self.etat_commande == "acces_salon":

                pass

    def envoi_message_clients(self, message):
        """
        Cette méthode parcourt tous les clients connectés
        et envoie le message spécifié à chacun d'eux.

        :param message: Le message à envoyer à tous les clients.
        """

        for ip_client, socket_client in self.clients.items():
            
            try:
                
                socket_client.sendall(message.encode())
                
            except Exception as erreur:
                
                print(f"\nErreur d'envoi du message à {ip_client}: {erreur}")

    def fermeture_connexions_clients(self):
        """
        Cette méthode parcourt tous les clients connectés
        et ferme leur connexion individuellement.
        """

        for ip_client, socket_client in self.clients.items():
            
            try:
                
                socket_client.close()
                
            except Exception as erreur:

                print(f"\nErreur de fermeture de la connexion avec "
                      f"{ip_client}: {erreur}")

    def gestion_clients(self, socket_client, adresse_client):
        """
        Cette méthode gère la communication avec un client spécifié
        en utilisant la socket du client.

        Elle gère l'authentification, l'inscription, les discussions publiques
        et tous types de requêtes différentes.

        :param socket_client: La socket du client.
        :param adresse_client: L'adresse IP du client.
        """

        ip_client = adresse_client[0]
        self.sessions[ip_client] = SessionClient()
        self.clients[ip_client] = socket_client

        print(f"\nClient connecté : {ip_client}")

        message_tampon = ""

        try:

            while True:

                donnees_client = socket_client.recv(1024)

                if not donnees_client:

                    print(f"\nClient déconnecté : {ip_client}")
                    break

                message_tampon += donnees_client.decode()

                while "\n" in message_tampon:

                    message_client, message_tampon = (
                        message_tampon.split("\n", 1))
                    message_client = message_client.strip()
                    print(f"\nMessage reçu de {ip_client}: {message_client}")

                    if message_client.startswith(
                            "[PROTOCOLE]AUTHENTIFICATION:"):

                        email, mot_de_passe = (
                            message_client.split(":")[1].split(","))

                        etat_sanction = self.verification_sanctions(email)

                        if etat_sanction == "BAN":

                            reponse = "BAN_CLIENT"

                        elif etat_sanction == "KICK":

                            reponse = "KICK_CLIENT"

                        else:

                            id_client, permission = (
                                self.authentification_client(email,
                                                             mot_de_passe))

                            if id_client is not None:

                                self.sessions[ip_client].authentifie = True
                                self.sessions[ip_client].id_client = id_client
                                self.sessions[ip_client].permission = (
                                    permission)
                                self.sessions[ip_client].email_client = email
                                self.enregistrer_historique_ip(email,
                                                               ip_client)
                                reponse = "SUCCES_AUTHENTIFICATION"

                            else:

                                reponse = "ECHEC_AUTHENTIFICATION"

                        socket_client.sendall(reponse.encode())

                    elif message_client.startswith(
                            "[PROTOCOLE]REQUETE_MEMBRES_SALONS_PUBLICS:"):

                        reponse = self.obtenir_membres_salons_publics()
                        socket_client.sendall(reponse.encode())

                    elif message_client.startswith(
                            "[PROTOCOLE]REQUETE_HISTORIQUE_SALONS_PUBLICS:"):

                        reponse = self.obtenir_historique_salons_publics()
                        socket_client.sendall(reponse.encode())

                    elif message_client.startswith(
                            "[PROTOCOLE]REQUETE_HISTORIQUE_SALONS_PRIVES:"):

                        id_client = self.sessions[ip_client].id_client
                        reponse = self.obtenir_historique_salons_prives(
                            id_client)
                        socket_client.sendall(reponse.encode())

                    elif message_client.startswith("[PROTOCOLE]INSCRIPTION:"):

                        infos = message_client.split(":")[1].split(",")
                        email = infos[2]
                        etat_sanction = self.verification_sanctions(email)

                        if etat_sanction == "BAN":

                            reponse = "BAN_CLIENT"

                        elif etat_sanction == "KICK":

                            reponse = "KICK_CLIENT"

                        else:

                            reponse = self.inscription_client(*infos)

                        socket_client.sendall(reponse.encode())

                    elif message_client.startswith("[PROTOCOLE]ACCES_SALON:"):

                        nom_salon = message_client.split(":")[1]
                        reponse = self.gestion_acces_salons(ip_client,
                                                            nom_salon)
                        socket_client.sendall(reponse.encode())

                    elif message_client.startswith(
                            "[PROTOCOLE]VERIFICATION_SALONS_AUTORISES:"):

                        id_client = self.sessions[ip_client].id_client
                        salons_autorises = (
                            self.obtenir_salons_autorises(id_client))
                        reponse = (f"[PROTOCOLE]LISTE_SALONS_AUTORISES:"
                                   f"{','.join(salons_autorises)}")
                        socket_client.sendall(reponse.encode())

                    elif message_client.startswith(
                            "[PROTOCOLE]DISCUSSION_PUBLIQUE:"):
                        _, nom_salon, contenu = message_client.split(":", 2)
                        id_client = self.sessions[ip_client].id_client
                        self.stocker_message_public(id_client, nom_salon,
                                                    contenu)
                        self.retransmettre_message_public(nom_salon, contenu,
                                                          id_client)

                    elif message_client.startswith(
                            "[PROTOCOLE]DISCUSSION_PRIVEE:"):

                        _, email_destinataire, contenu = message_client.split(
                            ":", 2)
                        email_expediteur = self.obtenir_email_par_id(
                            self.sessions[ip_client].id_client)
                        self.envoi_message_prive(email_expediteur,
                                                 email_destinataire, contenu)

                    else:

                        reponse = f"Message reçu, client {ip_client} !\n"
                        socket_client.sendall(reponse.encode())

        except Exception as erreur:

            print(f"\nErreur avec le client {ip_client}: {erreur}")

        finally:

            socket_client.close()

            if ip_client in self.sessions:

                del self.sessions[ip_client]

            if ip_client in self.clients:

                del self.clients[ip_client]

    def enregistrer_historique_ip(self, email, ip_client):
        """
        Cette méthode enregistre l'adresse IP d'un client dans l'historique,
        associée à son adresse e-mail, si elle n'existe pas déjà.

        :param email: L'adresse e-mail du client.
        :param ip_client: L'adresse IP du client.
        """

        with self.lien_mysql.cursor() as curseur:

            curseur.execute("""
                INSERT INTO historique_ip (email_client, ip_client)
                SELECT * FROM (SELECT %s, %s) AS tmp
                WHERE NOT EXISTS (
                    SELECT email_client, ip_client FROM historique_ip
                    WHERE email_client = %s AND ip_client = %s
                )
            """, (email, ip_client, email, ip_client))

            self.lien_mysql.commit()

    def obtenir_membres_salons_publics(self):
        """
        Cette méthode récupère la liste des membres pour chaque salon public
        sous forme de chaînes de caractères formatées.

        :return: Une chaîne de caractères contenant la liste des membres
        des salons publics.
        """

        try:

            with self.lien_mysql.cursor() as curseur:

                curseur.execute("""
                    SELECT nom_salon, GROUP_CONCAT(CONCAT(
                    nom, ' ', prenom, ':', email)) 
                    AS membres FROM membres_salons_publics 
                    JOIN clients 
                    ON membres_salons_publics.id_client = clients.id_client 
                    JOIN salons_publics 
                    ON membres_salons_publics.id_salon_public = 
                    salons_publics.id_salon_public GROUP BY nom_salon
                """)

                resultats = curseur.fetchall()
                resultats_json = json.dumps(resultats)
                print(resultats_json)
                return (f"[PROTOCOLE]LISTE_MEMBRES_SALONS_PUBLICS:"
                        f"{resultats_json}\n").rstrip()

        except Exception as erreur:

            print(
                f"\nErreur de récupération des membres des salons : {erreur}")
            return "[PROTOCOLE]ERREUR_MEMBRES_SALONS"

    def stocker_message_public(self, id_client, nom_salon, contenu):
        """
        Cette méthode stocke un message public dans la base de données
        avec les informations fournies.

        :param id_client: L'ID du client qui envoie le message.
        :param nom_salon: Le nom du salon public où le message est envoyé.
        :param contenu: Le contenu du message.
        """

        try:

            with self.lien_mysql.cursor() as curseur:

                curseur.execute("""
                    INSERT INTO messages 
                    (id_client, contenu, horodatage, id_salon_public)
                    SELECT %s, %s, NOW(), id_salon_public
                    FROM salons_publics
                    WHERE nom_salon = %s
                """, (id_client, contenu, nom_salon))
                self.lien_mysql.commit()

        except Exception as erreur:

            print(f"\nErreur lors de l'insertion du message : {erreur}")

    def obtenir_nom_prenom_client(self, id_client):
        """
        Cette méthode récupère le nom et le prénom d'un client
        à partir de son ID.

        :param id_client: L'ID du client.
        :return: Une chaîne de caractères au format "nom/prénom" du client.
        """

        with self.lien_mysql.cursor() as curseur:

            curseur.execute(
                "SELECT nom, prenom FROM clients WHERE id_client = %s",
                (id_client,))
            nom, prenom = curseur.fetchone()
            return f"{nom}/{prenom}"

    def retransmettre_message_public(self, nom_salon, contenu, id_client):
        """
        Cette méthode formate un message public avec les informations fournies
        (nom du salon, contenu, ID du client) et le retransmet 
        à tous les clients autorisés.

        :param nom_salon: Le nom du salon public où le message est envoyé.
        :param contenu: Le contenu du message.
        :param id_client: L'ID du client qui envoie le message.
        """

        nom_prenom = self.obtenir_nom_prenom_client(id_client)
        horodatage = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_formate = f"[{horodatage}] {nom_prenom} : {contenu}"

        for ip_client, session in self.sessions.items():

            try:

                socket_client = self.clients[ip_client]

                if nom_salon == "General":

                    socket_client.sendall(
                        f"[PROTOCOLE]MESSAGE_CHAT:"
                        f"{nom_salon}:{message_formate}".encode())

                elif self.verifier_acces_salon_public(session.id_client,
                                                      nom_salon):

                    socket_client.sendall(
                        f"[PROTOCOLE]MESSAGE_CHAT:"
                        f"{nom_salon}:{message_formate}".encode())

            except Exception as erreur:

                print(
                    f"\nErreur de la retransmission à {ip_client}: {erreur}")

    def obtenir_historique_salons_publics(self):
        """
        Cette méthode récupère l'historique des messages des salons publics,
        sous forme de paires (nom_salon, contenu) dans une liste.

        :return: Une chaîne de caractères contenant l'historique
        des messages des salons publics.
        """

        try:

            with self.lien_mysql.cursor() as curseur:

                curseur.execute("""
                    SELECT nom_salon, contenu
                    FROM messages
                    JOIN salons_publics ON 
                    messages.id_salon_public = salons_publics.id_salon_public
                """)
                resultats = curseur.fetchall()
                resultats_json = json.dumps(resultats)
                return (f"[PROTOCOLE]LISTE_MESSAGES_PUBLICS:"
                        f"{resultats_json}\n").rstrip()

        except Exception as erreur:

            print(
                f"\nErreur de récupération de l'historique public : {erreur}")
            return "[PROTOCOLE]ERREUR_HISTORIQUE_PUBLIC"

    def obtenir_historique_salons_prives(self, email_client):
        """
        Cette méthode récupère l'historique des messages des salons privés
        dans lesquels le client spécifié est impliqué, sous forme de paires
        (contenu, horodatage) dans une liste, triée par horodatage.

        :param email_client: L'adresse e-mail du client.
        :return: Une chaîne de caractères contenant l'historique d
        es messages des salons privés.
        """

        try:

            with self.lien_mysql.cursor() as curseur:

                curseur.execute("""
                    SELECT contenu, horodatage 
                    FROM messages
                    JOIN salons_prives ON 
                    messages.id_salon_prive = salons_prives.id_salon_prive 
                    WHERE email_participant_1 = %s OR email_participant_2 = %s 
                    ORDER BY horodatage
                """, (email_client, email_client))
                resultats = curseur.fetchall()
                return f"[PROTOCOLE]LISTE_MESSAGES_PRIVES:{resultats}\n"

        except Exception as erreur:

            print(
                f"\nErreur de récupération de l'historique privé : {erreur}")
            return "[PROTOCOLE]ERREUR_HISTORIQUE_PRIVE"

    def est_banni(self, email, ip_client):
        """
        Cette méthode vérifie si un client est actuellement banni
        en se basant sur son adresse e-mail et son adresse IP.
        Elle renvoie True si le client est banni et False sinon.

        :param email: L'adresse e-mail du client.
        :param ip_client: L'adresse IP du client.
        :return: True si le client est banni, False sinon.
        """

        with self.lien_mysql.cursor() as curseur:
            curseur.execute("""
                SELECT COUNT(*) FROM sanctions
                WHERE (email_client = %s OR ip_client = %s) 
                AND type_sanction = 'ban'
            """, (email, ip_client))
            (count,) = curseur.fetchone()
            return count > 0
        
    def est_kick(self, email_client, type_sanction):
        """
        Cette méthode consulte la base de données pour vérifier si le client
        spécifié est actuellement sous une sanction de type "kick"
        et, le cas échéant, si cette sanction est encore active.

        :param email_client: L'adresse e-mail du client à vérifier.
        :param type_sanction: Le type de sanction à vérifier ('kick').

        :return: Un tuple (est_sous_sanction, date_expiration) où :
            - est_sous_sanction est True si le client est sous sanction,
            sinon False.
            - date_expiration est la date d'expiration de la sanction
            si elle est à durée définie, sinon None.
        """

        with self.lien_mysql.cursor() as curseur:

            curseur.execute("""
                SELECT horodatage_sanction, duree_sanction FROM sanctions 
                WHERE email_client = %s AND type_sanction = 'kick'
            """, (email_client, type_sanction))
            resultat = curseur.fetchone()

            if resultat:

                horodatage_sanction, duree_sanction = resultat

                if duree_sanction is None:

                    return True, None  # Sanction à durée indéfinie

                else:

                    expiration_duree = horodatage_sanction + (
                        datetime.timedelta(seconds=duree_sanction))

                    if expiration_duree > datetime.datetime.now():

                        return True, expiration_duree  # Sanction non expirée

                    else:

                        return False, None  # Sanction expirée

            return False, None  # Pas de sanction

    def creation_salon_prive(self, email_client1, email_client2):
        """
        Cette méthode crée un salon de discussion privée en enregistrant
        les adresses e-mail des deux clients participants
        dans la base de données.

        :param email_client1: L'adresse e-mail du premier client participant.
        :param email_client2: L'adresse e-mail du deuxième client participant.
        :return: L'ID du salon de discussion privée créé.
        """

        with self.lien_mysql.cursor() as curseur:
            
            curseur.execute("""
                INSERT INTO salons_prives 
                (email_participant_1, email_participant_2)
                VALUES (%s, %s)
            """, (email_client1, email_client2))
            self.lien_mysql.commit()
            curseur.execute("SELECT LAST_INSERT_ID()")
            id_salon_prive = curseur.fetchone()[0]
            return id_salon_prive

    def envoi_message_prive(self, email_expediteur, email_destinataire, 
                            message):
        """
        Cette méthode envoie un message privé entre deux clients en utilisant 
        leurs adresses e-mail. Elle crée également un salon de discussion 
        privée si nécessaire.

        :param email_expediteur: L'adresse e-mail de l'expéditeur du MP.
        :param email_destinataire: L'adresse e-mail du destinataire du MP.
        :param message: Le contenu du MP.
        """
        
        if email_expediteur and email_destinataire:
            
            id_salon_prive = self.obtenir_creation_salon_prive(
                email_expediteur, email_destinataire)

            with self.lien_mysql.cursor() as curseur:
                
                curseur.execute("""
                    INSERT INTO messages 
                    (id_client, contenu, horodatage, id_salon_prive)
                    VALUES ((SELECT id_client FROM clients WHERE email = %s), 
                    %s, NOW(), %s)
                """, (email_expediteur, message, id_salon_prive))
                self.lien_mysql.commit()

            self.retransmettre_message_prive(email_expediteur, 
                                             email_destinataire, message)

        else:
            
            print("\nErreur : un des emails est introuvable.")

    def retransmettre_message_prive(self, email_expediteur, email_destinataire,
                                    contenu):
        """
        Cette méthode formate un message privé avec les informations fournies
        (adresse e-mail de l'expéditeur, adresse e-mail du destinataire,
        contenu) et le retransmet au client destinataire spécifié.

        :param email_expediteur: L'adresse e-mail de l'expéditeur du MP.
        :param email_destinataire: L'adresse e-mail du destinataire du MP.
        :param contenu: Le contenu du MP.
        """

        message_formate = f"[MP de {email_expediteur}] {contenu}"
        
        for ip_client, session in self.sessions.items():
            
            if session.email_client == email_destinataire:
                
                try:
                    
                    socket_client = self.clients[ip_client]
                    socket_client.sendall(
                        f"[PROTOCOLE]NOUVEAU_MESSAGE_PRIVE:"
                        f"{email_expediteur}:{message_formate}".encode())
                    
                except Exception as erreur:
                    
                    print(f"\nErreur lors de l'envoi du MP à "
                          f"{ip_client}: {erreur}")

    def obtenir_email_par_id(self, id_client):
        """
        Obtenir l'adresse e-mail d'un client par son ID.

        Cette méthode récupère l'adresse e-mail d'un client à partir de son ID.

        :param id_client: L'ID du client.
        :return: L'adresse e-mail du client ou None si non trouvée.
        """

        with self.lien_mysql.cursor() as curseur:
            
            curseur.execute("SELECT email FROM clients WHERE id_client = %s",
                            (id_client,))
            resultat = curseur.fetchone()
            return resultat[0] if resultat else None

    def obtenir_creation_salon_prive(self, email_client1, email_client2):
        """
        Cette méthode vérifie si un salon de discussion privée existe déjà
        entre les deux clients en utilisant leurs adresses e-mail.
        Si le salon existe, son ID est renvoyé. Sinon, un nouveau
        salon de discussion privée est créé et son ID est renvoyé.

        :param email_client1: L'adresse e-mail du premier client participant.
        :param email_client2: L'adresse e-mail du deuxième client participant.
        :return: L'ID du salon de discussion privée existant ou créé.
        """

        with self.lien_mysql.cursor() as curseur:
            
            curseur.execute("""
                SELECT id_salon_prive
                FROM salons_prives
                WHERE (email_participant_1 = %s AND email_participant_2 = %s)
                   OR (email_participant_1 = %s AND email_participant_2 = %s)
            """, (email_client1, email_client2, email_client2, email_client1))
            resultat = curseur.fetchone()
            
            if resultat:
                
                return resultat[0]
            
            else:
                
                return self.creation_salon_prive(email_client1, email_client2)

    def ajouter_acces_salon_public(self, id_client, nom_salon):
        """
        Cette méthode permet à un client d'obtenir l'accès à un salon public
        spécifique en utilisant son ID et le nom du salon. Si le client
        n'a pas déjà accès au salon, l'accès est ajouté.

        :param id_client: L'ID du client auquel ajouter l'accès.
        :param nom_salon: Le nom du salon public auquel ajouter l'accès.
        """

        try:

            with self.lien_mysql.cursor() as curseur:

                if not self.verifier_acces_salon_public(id_client, nom_salon):

                    curseur.execute("""
                        INSERT INTO 
                        membres_salons_publics (id_client, id_salon_public) 
                        SELECT %s, id_salon_public 
                        FROM salons_publics WHERE nom_salon = %s
                    """, (id_client, nom_salon))
                    self.lien_mysql.commit()

        except Exception as erreur:

            print(f"\nErreur lors de l'ajout de l'accès au salon : {erreur}")

    def verifier_acces_salon_public(self, id_client, nom_salon):
        """
        Vérifie si un client a accès à un salon public.

        :param id_client: L'ID du client à vérifier.
        :param nom_salon: Le nom du salon public à vérifier.
        :return: True si le client a accès au salon, False sinon.
        """

        try:

            with self.lien_mysql.cursor() as curseur:

                curseur.execute("""
                    SELECT COUNT(*) FROM membres_salons_publics
                    JOIN salons_publics ON 
                    membres_salons_publics.id_salon_public = 
                    salons_publics.id_salon_public 
                    WHERE id_client = %s AND nom_salon = %s
                """, (id_client, nom_salon))
                (count,) = curseur.fetchone()
                print(f"\nNombre de correspondances trouvées: {count}")
                return count > 0

        except Exception as erreur:

            print(f"\nErreur de la vérification de l'accès au salon : "
                  f"{erreur}")
            return False

    def obtenir_salons_autorises(self, id_client):
        """
        Obtient la liste des salons publics auxquels un client a accès.

        :param id_client: L'ID du client dont on veut connaître
        les salons autorisés.
        :return: Une liste des noms des salons publics auxquels
        le client a accès.
        """

        try:

            with self.lien_mysql.cursor() as curseur:

                curseur.execute("""
                    SELECT nom_salon FROM salons_publics
                    JOIN membres_salons_publics ON 
                    salons_publics.id_salon_public = 
                    membres_salons_publics.id_salon_public
                    WHERE id_client = %s
                """, (id_client,))
                resultats = curseur.fetchall()
                return [nom_salon for (nom_salon,) in resultats]

        except Exception as erreur:

            print(
                f"\nErreur de l'obtention des salons accessibles : {erreur}")
            return []

    def gestion_acces_salons(self, ip_client, nom_salon):
        """
        Gère l'accès d'un client à un salon.

        :param ip_client: L'adresse IP du client.
        :param nom_salon: Le nom du salon auquel le client veut accéder.
        :return: Un message indiquant si l'accès a été accordé,
        refusé ou si le salon est inconnu.
        """

        with self.verrou_requete_acces:

            id_client = self.sessions[ip_client].id_client
            email_client = self.sessions[ip_client].email_client

            if self.verifier_acces_salon_public(id_client, nom_salon):

                return f"[PROTOCOLE]ACCES_DEJA_ACCORDE:{nom_salon}"

            if nom_salon == "Blabla":

                self.ajouter_acces_salon_public(id_client, nom_salon)
                return "[PROTOCOLE]ACCES_ACCORDE:Blabla"

            elif nom_salon in ["Comptabilite", "Informatique", "Marketing"]:

                self.etat_commande = "salon_access"

                reponse = input(
                    f"Accorder l'accès au salon {nom_salon} à "
                    f"{ip_client}, {email_client} ? [O/N] : ")

                if reponse.upper() == "O":

                    self.ajouter_acces_salon_public(id_client, nom_salon)
                    self.etat_commande = "commande"
                    return f"[PROTOCOLE]ACCES_ACCORDE:{nom_salon}"

                else:

                    self.etat_commande = "commande"
                    return f"[PROTOCOLE]ACCES_REFUSE:{nom_salon}"

            else:

                return "[PROTOCOLE]SALON_INCONNU"


class SessionClient:
    """
    Définition d'une classe de gestion des sessions clients.
    """

    def __init__(self, authentifie=False, id_client=None, permission=None,
                 email_client=None):
        self.authentifie = authentifie
        self.id_client = id_client
        self.permission = permission
        self.email_client = email_client


# Paramètres de configuration du serveur
hote_init, port_init = '0.0.0.0', 24793

# Paramètres de connexion à la base de données
mysql_init = {
    'host': 'localhost',
    'port': 3306,
    'user': 'serveur',
    'password': 'sae302',
    'db': 'sae302',
}


def execution_programme():
    """
    Fonction principale pour exécuter le serveur de messagerie.
    Crée une instance du serveur de messagerie en utilisant les paramètres
    d'hôte, de port et de base de données spécifiés, puis démarre le serveur.
    """

    serveur_messagerie = ServeurDeMessagerie(hote_init, port_init, mysql_init)
    serveur_messagerie.demarrage_serveur()


if __name__ == '__main__':
    execution_programme()
