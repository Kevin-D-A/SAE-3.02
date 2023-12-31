from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton,
                             QVBoxLayout, QWidget, QLineEdit, QLabel,
                             QMessageBox, QSizePolicy, QTabWidget, QListView,
                             QFrame, QLCDNumber, QMenuBar, QStatusBar)
from PyQt6.QtCore import pyqtSignal, QObject, QRect, QStringListModel
from PyQt6.QtGui import QAction
import threading
import socket
import json
import sys
import re


class ClientServeur(QObject):
    """
    Classe représentant la gestion de la communication client-serveur.
    Cette classe gère la communication entre le client et le serveur,
    émet des signaux en cas de réponse, de succès de connexion ou de
    perte de connexion.
    """

    signal_reponse = pyqtSignal(str)
    signal_connexion_echouee = pyqtSignal()
    signal_connexion_reussie = pyqtSignal()
    signal_connexion_perdue = pyqtSignal()

    def __init__(self):
        """
        Constructeur de la classe ClientServeur.
        """

        super().__init__()
        self.hote = None
        self.port = None
        self.socket_client = None

    def ecoute_serveur(self):
        """
        Démarre l'écoute du serveur pour recevoir des données.
        En cas de perte de connexion, émet le signal signal_connexion_perdue.

        :exception: Génère des exceptions liées aux pertes, refus de connexion.
        """

        try:

            self.socket_client = socket.create_connection((self.hote,
                                                           self.port))
            self.signal_connexion_reussie.emit()

            while True:

                donnees = self.socket_client.recv(1024)

                if not donnees:

                    raise ConnectionError("Connexion au serveur perdue.")

                message = donnees.decode()
                self.signal_reponse.emit(message)

        except ConnectionRefusedError:

            self.signal_connexion_echouee.emit()

        except ConnectionError:

            self.signal_connexion_perdue.emit()

        finally:

            if self.socket_client:

                self.socket_client.close()

    def connexion_serveur_client(self, hote, port):
        """
        Établit une connexion au serveur avec l'adresse et le port donnés.
        Démarre un thread pour l'écoute du serveur.

        :param hote: L'adresse IP ou le nom d'hôte du serveur.
        :param port: Le numéro de port du serveur.
        """

        self.hote = hote
        self.port = port
        threading.Thread(target=self.ecoute_serveur, daemon=True).start()

    def envoi_message_serveur(self, message):
        """
        Envoie un message au serveur avec un délimiteur à la fin.

        :param message: Le message à envoyer au serveur.

        """

        if self.socket_client:

            delimiteur_message = message + "\n"
            self.socket_client.sendall(delimiteur_message.encode())


class InterfaceAccueil(QMainWindow):
    """
    Classe représentant l'interface d'accueil de l'application client.
    Cette interface permet à l'utilisateur de se connecter au serveur,
    de s'authentifier, de s'inscrire et de démarrer l'application principale.
    """

    def __init__(self):
        """
         Constructeur de la classe InterfaceAccueil.
        """

        super().__init__()
        self.client = ClientServeur()
        self.client.signal_connexion_perdue.connect(
            self.retour_vers_fenetre_accueil)
        self.interface_accueil = None
        self.widget_accueil = None
        self.ip_serveur = None
        self.valeur_ip_serveur = ""
        self.port_serveur = None
        self.valeur_port_serveur = ""
        self.bouton_connexion = None
        self.bouton_authentification = None
        self.email_authentification = None
        self.motdepasse_authentification = None
        self.bouton_inscription = None
        self.nom_inscription = None
        self.prenom_inscription = None
        self.email_inscription = None
        self.motdepasse_inscription = None
        self.fenetre_principale = None
        self.connexion_etablie = False
        self.client.signal_connexion_echouee.connect(
            self.connexion_serveur_echouee)
        self.client.signal_connexion_reussie.connect(
            self.connexion_serveur_reussie)
        self.initialisation_interface_accueil()

    def initialisation_interface_accueil(self):
        """
        Initialise l'interface utilisateur de l'accueil.

        Configure le titre de la fenêtre, crée un layout de type QVBoxLayout,
        et défini ce layout comme le layout principal du widget central
        de la fenêtre.

        Enfin, lance l'initialisation de la fenêtre d'accueil.
        """

        self.setWindowTitle('Accueil')
        self.interface_accueil = QVBoxLayout()
        self.widget_accueil = QWidget()
        self.widget_accueil.setLayout(self.interface_accueil)
        self.setCentralWidget(self.widget_accueil)
        self.initialisation_fenetre_accueil()

    def activation_boutons_accueil(self, activer):
        """
        Active ou désactive les boutons d'authentification
        et d'inscription de l'interface d'accueil.

        Si les boutons d'authentification et d'inscription existent
        dans l'interface, cette méthode permet de les activer ou de
        les désactiver en fonction de la valeur du paramètre 'activer'.

        :param activer: Un booléen indiquant s'il faut activer (True)
        ou désactiver (False) les boutons.
        """

        if hasattr(self, 'bouton_authentification'):

            self.bouton_authentification.setEnabled(activer)

        if hasattr(self, 'bouton_inscription'):

            self.bouton_inscription.setEnabled(activer)

    def activation_champs_connexion_accueil(self, activer):
        """
        Active ou désactive les champs de saisie d'adresse IP
        et de port dans l'interface d'accueil.

        Cette méthode permet d'activer ou de désactiver les champs
        de saisie d'adresse IP et de port en fonction de la valeur
        du paramètre 'activer'.

        :param activer: Un booléen indiquant s'il faut activer (True)
        ou désactiver (False) les champs.
        """

        self.ip_serveur.setEnabled(activer)
        self.port_serveur.setEnabled(activer)

    def reinitialisation_affichage(self):
        """
        Réinitialise l'affichage de l'interface en supprimant
        tous les éléments enfants.

        Cette méthode supprime tous les éléments enfants de l'interface
        d'accueil afin de réinitialiser l'affichage.
        """

        while self.interface_accueil.count():

            enfant = self.interface_accueil.takeAt(0)

            if enfant.widget():

                enfant.widget().deleteLater()

    def initialisation_fenetre_accueil(self):
        """
        Initialise la fenêtre d'accueil en créant et affichant
        les éléments nécessaires.

        Cette méthode configure et affiche les éléments de l'interface
        d'accueil tels que les champs de saisie d'adresse IP et de port,
        les boutons de connexion, d'authentification et d'inscription
        en fonction de l'état de la connexion au serveur.
        """

        self.setFixedSize(219, 190)
        self.reinitialisation_affichage()
        self.ip_serveur = QLineEdit(self)
        self.ip_serveur.setPlaceholderText('IP')
        self.ip_serveur.setText(self.valeur_ip_serveur)
        self.interface_accueil.addWidget(self.ip_serveur)
        self.port_serveur = QLineEdit(self)
        self.port_serveur.setPlaceholderText('Port')
        self.port_serveur.setText(self.valeur_port_serveur)
        self.interface_accueil.addWidget(self.port_serveur)
        self.bouton_connexion = QPushButton('Connexion', self)
        self.bouton_connexion.clicked.connect(self.connexion_serveur)
        self.interface_accueil.addWidget(self.bouton_connexion)
        self.bouton_authentification = QPushButton('Authentification', self)
        self.bouton_authentification.clicked.connect(
            self.initialisation_fenetre_authentification)
        self.interface_accueil.addWidget(self.bouton_authentification)
        self.bouton_inscription = QPushButton('Inscription', self)
        self.bouton_inscription.clicked.connect(
            self.initialisation_fenetre_inscription)
        self.interface_accueil.addWidget(self.bouton_inscription)

        if self.connexion_etablie:

            self.activation_champs_connexion_accueil(False)
            self.bouton_connexion.setText("Déconnexion")

        else:

            self.activation_champs_connexion_accueil(True)
            self.bouton_connexion.setText("Connexion")

        self.activation_boutons_accueil(self.connexion_etablie)

    def connexion_serveur(self):
        """
        Tente d'établir ou de fermer une connexion avec le serveur
        en fonction de l'état actuel.

        Si aucune connexion n'est établie, cette méthode tente de se
        connecter au serveur en utilisant les informations d'adresse IP
        et de port saisies. Elle effectue des vérifications sur l'adresse IP
        et le port pour s'assurer qu'ils sont valides. En cas d'erreur, elle
        affiche des messages d'erreur appropriés à l'utilisateur.

        Si une connexion est déjà établie, cette méthode ferme
        la connexion déjà existante.

        :exception ValueError: Si le port saisi n'est pas un nombre valide.
        :exception Exception: Si une erreur de connexion inattendue se produit,
        elle est capturée et affiche un message d'erreur générique.
        """

        try:

            if not self.connexion_etablie:

                hote = self.ip_serveur.text()
                port_str = self.port_serveur.text()

                if not hote or not port_str:
                    QMessageBox.critical(
                        self, "Erreur",
                        "Veuillez remplir les champs IP et Port")
                    return

                ip_pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"

                if not re.match(ip_pattern, hote):
                    QMessageBox.critical(self, "Erreur",
                                         "L'adresse IP n'est pas valide")
                    return

                if not port_str.isdigit() or not (0 <= int(port_str) <= 65535):
                    QMessageBox.critical(
                        self, "Erreur",
                        "Le port doit être un nombre entre 0 et 65535")
                    return

                port = int(port_str)
                self.valeur_ip_serveur = hote
                self.valeur_port_serveur = str(port)
                self.client.connexion_serveur_client(hote, port)

            else:

                self.deconnexion_serveur()

        except ValueError:

            QMessageBox.critical(self, "Erreur", "Le port doit être un nombre")

        except Exception as erreur:

            QMessageBox.critical(self, "Erreur de connexion.", str(erreur))

    def connexion_serveur_echouee(self):
        """
        Gère les actions à effectuer en cas d'échec de connexion au serveur.

        Affiche un message d'erreur indiquant que la connexion au serveur
        est impossible. Réactive les champs d'adresse IP et de port,
        met à jour le texte du bouton de connexion et désactive les
        autres boutons de l'interface.
        """

        QMessageBox.critical(self, "Connexion échouée",
                             "Connexion au serveur impossible")
        self.activation_champs_connexion_accueil(True)
        self.bouton_connexion.setText("Connexion")
        self.connexion_etablie = False
        self.activation_boutons_accueil(False)

    def connexion_serveur_reussie(self):
        """
        Gère les actions à effectuer en cas de réussite de la connexion
        au serveur.

        Met à jour l'état de connexion en tant que "établie", désactive
        les champs d'adresse IP et de port, met à jour le texte du bouton
        de connexion en "Déconnexion" et active les autres boutons
        de l'interface.
        """

        self.connexion_etablie = True
        self.activation_champs_connexion_accueil(False)
        self.bouton_connexion.setText("Déconnexion")
        self.activation_boutons_accueil(True)

    def deconnexion_serveur(self):
        """
        Ferme la connexion avec le serveur.

        Si une connexion au serveur est établie, cette méthode ferme la
        connexion existante et réinitialise l'état de connexion, active
        les champs d'adresse IP et de port, met à jour le texte  du bouton
        de connexion en "Connexion", réinitialise  les valeurs d'adresse IP
        et de port, et désactive les autres boutons de l'interface.

        Affiche également une notification de déconnexion.
        """

        if self.client.socket_client:
            self.client.socket_client.close()

        self.connexion_etablie = False
        self.activation_champs_connexion_accueil(True)
        self.bouton_connexion.setText("Connexion")
        self.valeur_ip_serveur = ""
        self.valeur_port_serveur = ""
        self.activation_boutons_accueil(False)
        QMessageBox.information(self, "Déconnexion", "Déconnecté du serveur")

    def creation_boutons(self, texte, fonction):
        """
        Crée un bouton avec le texte donné et connecte une fonction
        à son signal de clic.

        :param texte: Le texte affiché sur le bouton.
        :param fonction: La fonction à appeler lorsque le bouton est cliqué.
        """

        bouton = QPushButton(texte, self)
        bouton.clicked.connect(fonction)
        self.interface_accueil.addWidget(bouton)

    def creation_champs_saisie(self, variable, indication,
                               mode=QLineEdit.EchoMode.Normal):
        """
        Crée un champ de saisie QLineEdit avec une indication facultative
        et un mode d'écho.

        :param variable: Le nom de la variable à laquelle le champ de saisie
        est associé.
        :param indication: Le texte d'indication (placeholder) affiché
        dans le champ.
        :param mode: Le mode d'écho du champ de saisie (par défaut, normal).
        """

        champ = QLineEdit(self)
        champ.setPlaceholderText(indication)
        champ.setEchoMode(mode)
        setattr(self, variable, champ)
        self.interface_accueil.addWidget(champ)

    def initialisation_fenetre_authentification(self):
        """
        Initialise la fenêtre d'authentification en réinitialisant
        l'affichage, créant des champs de saisie pour l'email et
        le mot de passe, ainsi que des boutons pour se connecter
        et revenir à la fenêtre d'accueil.
        """

        self.reinitialisation_affichage()
        self.creation_champs_saisie('email_authentification',
                                    'Email')
        self.creation_champs_saisie('motdepasse_authentification',
                                    'Mot de passe',
                                    QLineEdit.EchoMode.Password)
        self.creation_boutons('Se connecter',
                              self.tentative_authentification)
        self.creation_boutons('Retour',
                              self.initialisation_fenetre_accueil)

    def tentative_authentification(self):
        """
        Tente de s'authentifier en utilisant l'email et le mot de passe
        saisis dans les champs correspondants.

        Récupère les valeurs des champs email_authentification et
        motdepasse_authentification, puis envoie un message au serveur
        contenant ces informations pour l'authentification.
        """

        email = self.email_authentification.text()
        mot_de_passe = self.motdepasse_authentification.text()

        if not email or not mot_de_passe:
            QMessageBox.critical(self, "Erreur", "Veuillez remplir les champs")
            return

        message = f"[PROTOCOLE]AUTHENTIFICATION:{email},{mot_de_passe}"
        self.client.envoi_message_serveur(message)

    def initialisation_fenetre_inscription(self):
        """
        Initialise la fenêtre d'inscription en réinitialisant l'affichage,
        créant des champs de saisie pour le nom, le prénom, l'email
        et le mot de passe, ainsi que des boutons pour s'inscrire et
        revenir à la fenêtre d'accueil.
        """

        self.reinitialisation_affichage()
        self.creation_champs_saisie('nom_inscription',
                                    'Nom')
        self.creation_champs_saisie('prenom_inscription',
                                    'Prénom')
        self.creation_champs_saisie('email_inscription',
                                    'Email')
        self.creation_champs_saisie('motdepasse_inscription',
                                    'Mot de passe',
                                    QLineEdit.EchoMode.Password)
        self.creation_boutons('S\'inscrire', self.tentative_inscription)
        self.creation_boutons('Retour', self.initialisation_fenetre_accueil)

    def tentative_inscription(self):
        """
         Tente de s'inscrire en utilisant les informations saisies
         dans les champs de nom, prénom, email et mot de passe.

         Récupère les valeurs des champs nom_inscription, prenom_inscription,
         email_inscription et motdepasse_inscription, puis envoie un message
         au serveur pour demander l'inscription.
         """

        nom = self.nom_inscription.text()
        prenom = self.prenom_inscription.text()
        email = self.email_inscription.text()
        mot_de_passe = self.motdepasse_inscription.text()

        if not nom or not mot_de_passe or not email:

            QMessageBox.critical(self, "Erreur d'inscription",
                                 "Tous les champs doivent être remplis.")
            return

        if not re.match(r'^[\w.-]+@[\w.-]+\.\w+$', email):

            QMessageBox.critical(self, "Erreur d'inscription",
                                 "Format d'adresse email invalide.")
            return

        message = (f"[PROTOCOLE]INSCRIPTION:"
                   f"{nom},{prenom},{email},{mot_de_passe},utilisateur")
        self.client.envoi_message_serveur(message)

    def gestion_reponses_serveur(self, message):
        """
        Gère les réponses reçues du serveur après l'envoi de demandes
        d'authentification, d'inscription ou d'autres requêtes.

        :param message: Le message reçu du serveur pour traitement.
        :type message: str

        Les actions suivantes sont effectuées en fonction du message reçu :

        - Si le message est "SUCCES_AUTHENTIFICATION", l'authentification est
        réussie, et une nouvelle fenêtre principale est affichée.

        - Si le message est "ECHEC_AUTHENTIFICATION", une fenêtre d'erreur
        d'authentification est affichée.

        - Si le message est "SUCCES_INSCRIPTION", l'inscription est réussie,
        et la fenêtre d'accueil est réinitialisée.

        - Si le message est "ECHEC_INSCRIPTION", une fenêtre d'erreur
        d'inscription est affichée.

        - Si le message est "[PROTOCOLE]ARRET_SERVEUR:", une notification
        d'arrêt du serveur est affichée.
        """

        if message == "SUCCES_AUTHENTIFICATION":

            print("Authentification réussie")
            self.client.signal_connexion_perdue.disconnect(
                self.retour_vers_fenetre_accueil)
            self.fenetre_principale = InterfacePrincipale(self, self.client)
            self.client.envoi_message_serveur(
                "[PROTOCOLE]VERIFICATION_SALONS_AUTORISES:")
            self.client.envoi_message_serveur(
                "[PROTOCOLE]REQUETE_MEMBRES_SALONS_PUBLICS:")
            self.fenetre_principale.show()
            self.hide()

        elif message == "ECHEC_AUTHENTIFICATION":

            QMessageBox.critical(self, "Erreur d'authentification",
                                 "Identifiants invalides !")
            print("Échec de l'authentification : Identifiants invalides !")

        elif message == "SUCCES_INSCRIPTION":

            self.initialisation_fenetre_accueil()
            print("Inscription réussie")

        elif message == "ECHEC_INSCRIPTION":

            QMessageBox.critical(self, "Erreur d'inscription",
                                 "Inscription non valide !")

        elif message == "BAN_CLIENT":

            QMessageBox.warning(self, "Sanction", "Vous êtes BAN !")
            self.deconnexion_serveur()

        elif message == "KICK_CLIENT":

            QMessageBox.warning(self, "Sanction", "Vous êtes KICK !")
            self.deconnexion_serveur()

        elif message == "[PROTOCOLE]ARRET_SERVEUR:":

            QMessageBox.warning(self, "Arrêt du serveur.",
                                "Le serveur va s'arrêter "
                                "dans quelques secondes.")

    def retour_vers_fenetre_accueil(self):
        """
        Gère le retour à la fenêtre d'accueil en cas de perte de connexion
        avec le serveur.

        Affiche une boîte de dialogue d'avertissement indiquant que la
        connexion avec le serveur a été perdue. Réinitialise l'interface
        d'accueil en appelant la méthode initialisation_fenetre_accueil.
        Rétablit les paramètres de connexion et d'interface par défaut.
        """

        QMessageBox.warning(self, "Connexion perdue",
                            "La connexion avec le serveur a été perdue.")
        self.show()
        self.initialisation_fenetre_accueil()
        self.connexion_etablie = False
        self.ip_serveur.clear()
        self.port_serveur.clear()
        self.bouton_connexion.setText("Connexion")
        self.activation_champs_connexion_accueil(True)
        self.activation_boutons_accueil(self.connexion_etablie)


class InterfacePrincipale(QMainWindow):
    """
    Classe représentant l'interface principale de l'application de messagerie.
    Cette interface permet à l'utilisateur de naviguer entre les salons
    de discussion, d'envoyer des messages, etc.

    :param interface_client: Instance de l'interface de connexion du client.
    :param client_serveur: Instance du client-serveur gérant la communication
    avec le serveur.
    """

    def __init__(self, interface_client, client_serveur):
        """
        Initialise une instance de l'interface principale.

        :param interface_client: Instance de l'interface de connexion client.
        :param client_serveur: Instance de la classe ClientServeur gérant
        la communication avec le serveur.
        """

        super().__init__()
        self.interface_client = interface_client
        self.client_serveur = client_serveur
        self.client_serveur.signal_connexion_perdue.connect(
            self.deconnexion_et_retour_fenetre_accueil)
        self.barre_menu = None
        self.barre_statut = None
        self.widget_principal = None
        self.label_messages_prives = None
        self.nombre_messages_prives = None
        self.liste_messages_prives = None
        self.separateur_horizontal_gauche = None
        self.bouton_deconnexion = None
        self.separateur_vertical_gauche = None
        self.widget_onglets = None
        self.onglet_general = None
        self.onglet_blabla = None
        self.onglet_comptabilite = None
        self.onglet_informatique = None
        self.onglet_marketing = None
        self.onglet_prive = None
        self.chat_general = None
        self.chat_blabla = None
        self.chat_comptabilite = None
        self.chat_informatique = None
        self.chat_marketing = None
        self.chat_prive = None
        self.champ_saisie = None
        self.bouton_envoyer = None
        self.separateur_vertical_droit = None
        self.label_membres_salon = None
        self.nombre_membres_salon = None
        self.liste_membres = None
        self.membres_par_salon = {}
        self.infos_membre = {}
        self.separateur_horizontal_droit = None
        self.bouton_theme = None
        self.theme_sombre = False
        self.client_serveur.signal_reponse.connect(
            self.gestion_reponses_serveur)
        self.salons_autorises = []
        self.modele_chat_general = QStringListModel()
        self.modele_chat_blabla = QStringListModel()
        self.modele_chat_comptabilite = QStringListModel()
        self.modele_chat_informatique = QStringListModel()
        self.modele_chat_marketing = QStringListModel()
        self.modele_chat_prive = QStringListModel()
        self.creation_barre_menu()
        self.initialisation_interface_principale(self)
        self.changement_theme()

    def creation_barre_menu(self):
        """
        Crée la barre de menu de l'interface principale.
        Cette barre de menu contient des options pour accéder à des
        liens externes (GitHub, E-Services) et pour afficher des informations
        sur l'application (À propos).
        """

        self.barre_menu = self.menuBar()
        menu_liens = self.barre_menu.addMenu("Liens")
        bouton_github = QAction("GitHub", self)
        bouton_github.triggered.connect(
            lambda: QMessageBox.information(
                self, "GitHub",
                "Lien vers le repository GitHub\nhttps://github.com"))
        menu_liens.addAction(bouton_github)
        bouton_eservices = QAction("E-Services", self)
        bouton_eservices.triggered.connect(
            lambda: QMessageBox.information(
                self, "E-Services",
                "Lien vers E-Services UHA\nhttps://www.e-services.uha.fr"))
        menu_liens.addAction(bouton_eservices)
        menu_infos = self.barre_menu.addMenu("Informations")
        bouton_apropos = QAction("À propos", self)
        bouton_apropos.triggered.connect(
            lambda: QMessageBox.information(
                self, "À propos",
                "Serveur de messagerie \nVersion 1.0"))
        menu_infos.addAction(bouton_apropos)

    def deconnexion_et_retour_fenetre_accueil(self):
        """
        Gère la déconnexion de l'utilisateur et le retour à la fenêtre
        d'accueil en cas de perte de connexion.

        Affiche un avertissement indiquant que la connexion avec le serveur
        a été perdue. Ferme la connexion avec le serveur en fermant le
        socket client, le déconnecte et ferme la fenêtre principale.
        Déconnecte également la méthode de gestion des réponses du serveur.
        Enfin, rappelle la méthode `retour_vers_fenetre_accueil` de
        l'interface de connexion du client.
        """

        QMessageBox.warning(self, "Connexion perdue",
                            "La connexion avec le serveur a été perdue.")

        if self.client_serveur.socket_client:

            self.client_serveur.socket_client.close()
            self.client_serveur.socket_client = None

        self.close()
        self.client_serveur.signal_reponse.disconnect(
            self.gestion_reponses_serveur)
        self.interface_client.retour_vers_fenetre_accueil()

    def changement_theme(self):
        """
        Gère le changement du thème entre le mode sombre et le mode clair
        de l'interface.

        Bascule l'état du thème (entre sombre et clair) en inversant la
        valeur actuelle. Si le thème sombre est activé, modifie la feuille
        de style de l'interface pour un fond sombre et du texte blanc.
        Si le thème sombre est désactivé, réinitialise la feuille de style
        pour l'apparence par défaut.
        """

        self.theme_sombre = not self.theme_sombre

        if self.theme_sombre:

            self.setStyleSheet("""
                QMainWindow {
                    background-color: #232323;
                }
                QMenuBar {
                    background-color: #333333;
                    color: #FFFFFF;
                }
                QMenuBar::item {
                    background-color: #333333;
                    color: #FFFFFF;
                }
                QTabWidget::pane {
                    background-color: #333333;
                    border: 1px solid #444444;
                }
                QTabBar::tab {
                    background-color: #333333;
                    color: white;
                    border: 1px solid #444444;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    padding: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #444444;
                }
                QMenuBar::item:selected {
                    background-color: #444444;
                }
                QStatusBar {
                    background-color: #333333;
                    color: #FFFFFF;
                }
                QPushButton {
                    background-color: #444444;
                    color: #FFFFFF;
                    border: 2px solid #333333;
                    border-radius: 5px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #555555;
                }
                QPushButton:pressed {
                    background-color: #333333;
                }
                QLabel {
                    color: #FFFFFF;
                }
                QListView {
                    background-color: #333333;
                    color: #FFFFFF;
                    border: 1px solid #444444;
                    border-radius: 5px;
                }
                QLineEdit {
                    background-color: #444444;
                    color: #FFFFFF;
                    border: 2px solid #333333;
                    border-radius: 5px;
                }
                QLCDNumber {
                    background-color: #444444;
                    color: #FFFFFF;
                    border: 2px solid #333333;
                    border-radius: 5px;
                }
            """)

        else:

            self.setStyleSheet("""
                QMainWindow {
                    background-color: #F5F5F5;
                }
                QMenuBar {
                    background-color: #E5E5E5;
                    color: #000000;
                }
                QMenuBar::item {
                    background-color: #E5E5E5;
                    color: #000000;
                }
                QTabWidget::pane {
                    background-color: #E5E5E5;
                    border: 1px solid #D5D5D5;
                }
                QTabBar::tab {
                    background-color: #E5E5E5;
                    color: black;
                    border: 1px solid #D5D5D5;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    padding: 4px;
                }
                QTabBar::tab:selected {
                    background-color: #D5D5D5;
                }
                QMenuBar::item:selected {
                    background-color: #D5D5D5;
                }
                QStatusBar {
                    background-color: #E5E5E5;
                    color: #000000;
                }
                QPushButton {
                    background-color: #D5D5D5;
                    color: #000000;
                    border: 2px solid #E5E5E5;
                    border-radius: 5px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: #C5C5C5;
                }
                QPushButton:pressed {
                    background-color: #E5E5E5;
                }
                QLabel {
                    color: #000000;
                }
                QListView {
                    background-color: #D5D5D5;
                    color: #000000;
                    border: 1px solid #C5C5C5;
                    border-radius: 5px;
                }
                QLineEdit {
                    background-color: #E5E5E5;
                    color: #000000;
                    border: 2px solid #D5D5D5;
                    border-radius: 5px;
                }
                QLCDNumber {
                    background-color: #E5E5E5;
                    color: #000000;
                    border: 2px solid #D5D5D5;
                    border-radius: 5px;
                }
            """)

    def demander_acces_salon(self, nom_salon):
        """
        Envoie une demande d'accès à un salon spécifique au serveur.

        Envoie un message au serveur pour demander l'accès au salon
        spécifié par `nom_salon`.

        :param nom_salon: Le nom du salon auquel l'accès est demandé.
        :type nom_salon: str
        """

        self.client_serveur.envoi_message_serveur(
            f"[PROTOCOLE]ACCES_SALON:{nom_salon}")

    def creer_onglet_salon(self, nom_salon):
        """
        Crée un onglet pour un salon de discussion et l'ajoute à
        l'interface principale.

        Crée un onglet contenant un chat et un bouton pour demander l'accès
        au salon, puis l'ajoute à la liste des onglets de l'interface
        principale. Le chat est désactivé pour les salons autres
        que "General" lors de la création.

        :param nom_salon: Le nom du salon de discussion à créer.
        :type nom_salon: str
        :return: L'onglet créé pour le salon de discussion.
        :rtype: QWidget
        """

        onglet = QWidget()
        disposition = QVBoxLayout(onglet)

        chat = QListView(onglet)
        chat.setEnabled(nom_salon == "General")
        disposition.addWidget(chat)

        bouton_acces = QPushButton(f"Demander l'accès à {nom_salon}", onglet)
        bouton_acces.clicked.connect(
            lambda: self.demander_acces_salon(nom_salon))
        disposition.addWidget(bouton_acces)

        self.widget_onglets.addTab(onglet, nom_salon)

        setattr(self, f"chat_{nom_salon.lower()}", chat)
        setattr(self, f"bouton_{nom_salon.lower()}", bouton_acces)

        return onglet

    def gestion_reponses_serveur(self, message):
        """
        Gère les réponses reçues du serveur en fonction
        du protocole de communication utilisé.

        Cette méthode est responsable de la gestion des différentes
        réponses reçues du serveur, en fonction des messages reçus.
        Elle analyse le message et effectue les actions appropriées
        en réponse, telles que l'affichage de messages, l'activation
        de salons, la mise à jour de la liste de membres, etc.

        :param message: Le message reçu du serveur.
        :type message: str
        :exception Exception: En cas d'erreur lors de la conversion
        des données des membres.
        """

        if message == "[PROTOCOLE]ARRET_SERVEUR:":

            QMessageBox.warning(self, "Arrêt du serveur.",
                                "Le serveur va bientôt s'arrêter !")

        elif message.startswith("[PROTOCOLE]LISTE_SALONS_AUTORISES"):
            salons_autorises = message.split(":")[1].split(",")
            self.activer_salons_autorises(salons_autorises)

        elif message.startswith("[PROTOCOLE]LISTE_MEMBRES_SALONS_PUBLICS:"):
            print(message)
            donnees = message.split(
                "[PROTOCOLE]LISTE_MEMBRES_SALONS_PUBLICS:")[1]
            print(donnees)
            messages = donnees.split('\n')

            for msg in messages:

                if not msg.strip():

                    continue

                try:

                    membres = json.loads(msg)
                    print(membres)
                    self.liste_membres_salons_publics(membres)
                    self.mettre_a_jour_liste_membres(None)

                except json.JSONDecodeError as erreur:

                    print(f"Erreur de décodage JSON: {erreur}")

        elif message.startswith("[PROTOCOLE]LISTE_MESSAGES_PUBLICS:"):
            self.historique_salons_publics(message.split(
                "[PROTOCOLE]LISTE_MESSAGES_PUBLICS:")[1])

        elif message.startswith("[PROTOCOLE]LISTE_MESSAGES_PRIVES:"):
            self.historique_salons_prives(message.split(':')[1])

        elif message.startswith("[PROTOCOLE]MESSAGE_CHAT"):
            _, nom_salon, contenu = message.split(":", 2)
            self.afficher_messages_utilisateurs(nom_salon, contenu)

        elif message.startswith("[PROTOCOLE]NOUVEAU_MESSAGE_PRIVE:"):
            _, expediteur, contenu = message.split(":", 2)
            self.ajouter_message_prive(expediteur, contenu)

        elif message.startswith("[PROTOCOLE]ACCES_ACCORDE"):

            nom_salon = message.split(":")[1]
            self.activer_salon(nom_salon)
            self.client_serveur.envoi_message_serveur(
                "[PROTOCOLE]REQUETE_MEMBRES_SALONS_PUBLICS:")

        elif message == "BAN_CLIENT":

            QMessageBox.warning(self, "Sanction", "Vous êtes BAN !")
            self.deconnexion_et_retour_fenetre_accueil()

        elif message == "KICK_CLIENT":

            QMessageBox.warning(self, "Sanction", "Vous êtes KICK !")
            self.deconnexion_et_retour_fenetre_accueil()

        elif message.startswith("[PROTOCOLE]ACCES_REFUSE"):

            nom_salon = message.split(":")[1]
            QMessageBox.critical(self, "Accès Refusé",
                                 f"Accès au salon {nom_salon} refusé.")

    def liste_membres_salons_publics(self, membres):
        """
        Met à jour la liste des membres par salon à partir des données reçues
        du serveur.

        Cette méthode prend en entrée les données des membres par salon reçues
        du serveur et met à jour la structure `self.membres_par_salon`.
        Elle parcourt les données, extrait le nom et l'e-mail de chaque membre,
        puis les ajoute à la liste des membres du salon correspondant. Les
        informations sur les membres sont également stockées dans le
        dictionnaire `self.infos_membre`.

        :param membres: Les données des membres par salon au format
        [(nom_salon, liste_membres_str)].
        :type membres: list
        """

        self.membres_par_salon.clear()
        self.infos_membre = {}

        for nom_salon, liste_membres_str in membres:

            liste_membres = []

            for membre_str in liste_membres_str.split(','):

                if membre_str:

                    nom_prenom, email = membre_str.split(":", 1)
                    liste_membres.append(nom_prenom)
                    self.infos_membre[nom_prenom] = email

            self.membres_par_salon[nom_salon] = liste_membres

    def mettre_a_jour_liste_membres(self, index):
        """
        Met à jour la liste des membres selon l'onglet actif.

        Si `index` n'est pas spécifié, l'index de l'onglet actif est utilisé.
        Affiche la liste des membres autorisés ou un message d'accès
        non autorisé.

        :param index: Index de l'onglet à mettre à jour (par défaut, actif).
        :type index: int or None
        """

        if index is None:

            index = self.widget_onglets.currentIndex()

        nom_salon = self.widget_onglets.tabText(index)

        if nom_salon in self.salons_autorises:

            membres = self.membres_par_salon.get(nom_salon, [])
            self.champ_saisie.setEnabled(True)
            self.bouton_envoyer.setEnabled(True)

        else:

            membres = ["Accès non autorisé"]
            self.nombre_membres_salon.display(0)
            self.champ_saisie.setEnabled(False)
            self.bouton_envoyer.setEnabled(False)

        self.nombre_membres_salon.display(len(membres))
        modele = QStringListModel(membres)
        self.liste_membres.setModel(modele)
        self.liste_membres.setEditTriggers(
            QListView.EditTrigger.NoEditTriggers)

    def historique_salons_publics(self, historique_json):
        """
        Met à jour l'historique des salons publics avec les messages reçus
        du serveur.

        Cette méthode prend en entrée l'historique des salons publics au format
        JSON et le convertit en une liste de tuples (nom_salon, contenu).
        Elle parcourt ensuite l'historique, récupère le contenu de chaque
        message et l'ajoute à la liste des messages actuels du salon
        correspondant.

        :param historique_json: L'historique des salons publics au format JSON.
        :type historique_json: str
        """

        try:
            historique = json.loads(historique_json)

        except json.JSONDecodeError as erreur:

            print(f"Erreur de décodage JSON: {erreur}")
            return

        for nom_salon, contenu in historique:

            chat = getattr(self, f"chat_{nom_salon.lower()}", None)

            if chat:

                messages_actuels = chat.model().stringList()
                messages_actuels.append(contenu)
                chat.model().setStringList(messages_actuels)

    def historique_salons_prives(self, historique):
        """
        Met à jour l'historique des messages privés avec les messages
        reçus du serveur.

        Cette méthode prend en entrée l'historique des messages privés
        sous forme de liste de messages et les ajoute à l'élément de liste
        des messages privés.

        :param historique: L'historique des messages privés.
        :type historique: list[str]
        """

        for message in historique:

            self.liste_messages_prives.addItem(message)

    def activer_salons_autorises(self, salons_autorises):
        """
        Active les salons autorisés à partir de la liste fournie.

        Cette méthode prend en entrée une liste de noms de salons
        autorisés et active chacun de ces salons en appelant la méthode
        `activer_salon` pour chaque nom de salon.

        :param salons_autorises: La liste des noms de salons autorisés.
        :type salons_autorises: list[str]
        """

        for nom_salon in salons_autorises:

            self.activer_salon(nom_salon)

    def activer_salon(self, nom_salon):
        """
        Active un salon spécifié.

        Cette méthode prend en entrée le nom d'un salon et l'active en rendant
        son chat disponible et en masquant le bouton d'accès. Si le nom du
        salon n'est pas déjà dans la liste des salons autorisés
        (`self.salons_autorises`), il est ajouté à cette liste.

        :param nom_salon: Le nom du salon à activer.
        :type nom_salon: str
        """

        chat = getattr(self, f"chat_{nom_salon.lower()}", None)
        bouton = getattr(self, f"bouton_{nom_salon.lower()}", None)

        if chat and bouton:

            chat.setEnabled(True)
            bouton.setVisible(False)

            if nom_salon not in self.salons_autorises:

                self.salons_autorises.append(nom_salon)

            self.mettre_a_jour_liste_membres(None)

    def initialiser_salons(self):
        """
        Initialise les onglets de salon, active le salon "General" par défaut.

        Cette méthode crée plusieurs onglets de salon en utilisant la méthode
        `creer_onglet_salon` pour les salons tels que "General", "Blabla",
        "Comptabilite", "Informatique", et "Marketing". Elle active le salon
        "General" par défaut.
        """

        self.onglet_general = self.creer_onglet_salon("General")
        self.onglet_general.setObjectName(u"onglet_general")
        self.onglet_blabla = self.creer_onglet_salon("Blabla")
        self.onglet_blabla.setObjectName(u"onglet_blabla")
        self.onglet_comptabilite = self.creer_onglet_salon("Comptabilite")
        self.onglet_comptabilite.setObjectName(u"onglet_comptabilite")
        self.onglet_informatique = self.creer_onglet_salon("Informatique")
        self.onglet_informatique.setObjectName(u"onglet_informatique")
        self.onglet_marketing = self.creer_onglet_salon("Marketing")
        self.onglet_marketing.setObjectName(u"onglet_marketing")
        self.activer_salon("General")

    def envoyer_saisie_utilisateur(self):
        """
        Envoie le message saisi par l'utilisateur au salon actuellement
        sélectionné.

        Cette méthode récupère le message saisi par l'utilisateur depuis
        le champ de saisie. Si le message n'est pas vide, elle détermine
        le protocole de discussion en fonction du salon actuellement
        sélectionné (public ou privé) et envoie le message au serveur avec
        le nom du salon et le contenu du message. Enfin, elle efface le
        champ de saisie.
        """

        message_utilisateur = self.champ_saisie.text()

        if message_utilisateur:

            nom_salon = self.widget_onglets.tabText(
                self.widget_onglets.currentIndex())

            if nom_salon in ["General", "Blabla", "Comptabilite",
                             "Informatique", "Marketing"]:

                protocole = "[PROTOCOLE]DISCUSSION_PUBLIQUE"
            else:

                protocole = "[PROTOCOLE]DISCUSSION_PRIVEE"

            self.client_serveur.envoi_message_serveur(
                f"{protocole}:{nom_salon}:{message_utilisateur}")
            self.champ_saisie.clear()

    def afficher_messages_utilisateurs(self, nom_salon, message):
        """
        Affiche un message dans la liste de messages du salon spécifié.

        Cette méthode prend en entrée le nom du salon `nom_salon` et le
        `message` à afficher. Elle récupère le modèle de liste de messages
        associé au salon et ajoute le message à la liste des messages actuels.
        Ensuite, elle met à jour le modèle de la liste de messages du salon
        et configure la liste pour qu'elle ne puisse pas être éditée par
        l'utilisateur.

        :param nom_salon: Le nom du salon où afficher le message.
        :type nom_salon: str
        :param message: Le message à afficher dans le salon.
        :type message: str
        """

        modele = getattr(self, f"modele_chat_{nom_salon.lower()}")
        print(modele)

        if not modele:

            return

        messages_actuels = modele.stringList()
        print(messages_actuels)
        messages_actuels.append(message)
        print(messages_actuels)
        modele.setStringList(messages_actuels)
        chat = getattr(self, f"chat_{nom_salon.lower()}")
        chat.setModel(modele)
        chat.setEditTriggers(QListView.EditTrigger.NoEditTriggers)

    def double_clic_membre_salon(self, index):

        """
        Gère l'événement de double-clic sur un membre d'un salon public
        en ouvrant un salon de discussion privée si l'adresse e-mail
        du membre est disponible.

        :param index: Index de l'élément sélectionné dans la liste des membres.
        :type index: QModelIndex
        """

        nom_membre = index.data()
        email_membre = self.infos_membre.get(nom_membre)

        if email_membre:

            self.ouvrir_salon_prive(email_membre, nouveau=True)

        else:

            print("Email du membre non trouvé.")

    def double_clic_message_prive(self, index):
        """
        Ouvre un salon de discussion privée en double-cliquant sur
        un message privé.

        :param index: Index de l'élément sélectionné dans la liste des
        messages privés.
        :type index: QModelIndex
        """

        nom_membre = index.data().split("\n")[0]
        self.ouvrir_salon_prive(nom_membre, nouveau=False)
        
    def ajouter_message_prive(self, expediteur, contenu):
        """
        Ajoute un nouveau message privé à la liste des messages privés.

        Cette méthode affiche le nom de l'expéditeur suivi de
        "NOUVEAU MESSAGE" dans la liste des messages privés pour indiquer
        un nouveau message non lu. Elle met également à jour le nombre de
        messages non lus.

        Si le salon de discussion privée avec l'expéditeur est déjà ouvert,
        le message est ajouté à l'historique du chat.

        :param expediteur: Nom de l'expéditeur du message privé.
        :type expediteur: str
        :param contenu: Contenu du message privé.
        :type contenu: str
        """

        nouveau_mp = f"{expediteur}\nNOUVEAU MESSAGE"
        self.liste_messages_prives.addItem(nouveau_mp)
        self.nombre_messages_prives.display(self.liste_messages_prives.count())

        if hasattr(self, f"chat_prive_{expediteur}"):

            chat_prive = getattr(self, f"chat_prive_{expediteur}")
            chat_prive.model().stringList().append(contenu)

    def envoyer_message_prive(self):
        """
        Envoie un message privé à un membre.

        Cette méthode envoie le message saisi par l'utilisateur à un membre 
        spécifié. Le nom du membre cible est obtenu à partir de l'onglet 
        actuellement sélectionné. Le message est envoyé au serveur en 
        utilisant le message protocole "[PROTOCOLE]DISCUSSION_PRIVEE".
        """
        
        message_utilisateur = self.champ_saisie.text()

        if message_utilisateur:

            nom_membre = self.widget_onglets.tabText(
                self.widget_onglets.currentIndex())
            self.client_serveur.envoi_message_serveur(
                f"[PROTOCOLE]DISCUSSION_PRIVEE:"
                f"{nom_membre}:{message_utilisateur}")
            self.champ_saisie.clear()
            
    def ouvrir_salon_prive(self, nom_membre, nouveau):
        """
        Ouvre un salon de discussion privée avec un membre.

        Cette méthode permet d'ouvrir un salon de discussion privée avec
        un membre spécifié. Si le salon n'existe pas encore, un nouvel onglet
        est créé pour la conversation privée. Si l'argument 'nouveau' est True,
        un message est envoyé au serveur pour récupérer l'historique de la
        conversation.

        :param nom_membre: Le nom du membre avec qui démarrer la conversation.
        :type nom_membre: str
        :param nouveau: Indique s'il s'agit d'une nouvelle conversation (True)
        ou non (False).
        :type nouveau: bool
        """

        for index in range(self.widget_onglets.count()):
            
            if self.widget_onglets.tabText(index) == nom_membre:
                
                self.widget_onglets.setCurrentIndex(index)
                return

        onglet = QWidget()
        disposition = QVBoxLayout(onglet)
        chat = QListView(onglet)
        disposition.addWidget(chat)
        self.widget_onglets.addTab(onglet, nom_membre)
        setattr(self, f"chat_prive_{nom_membre}", chat)

        if nouveau:

            self.client_serveur.envoi_message_serveur(
                f"[PROTOCOLE]HISTORIQUE_PRIVE:{nom_membre}")

    def initialisation_interface_principale(self, fenetre_interface_client):
        """
        Initialise l'interface principale de l'application client.

        Cette méthode configure les éléments de l'interface principale de
        l'application client, notamment la barre de menu, la barre de statut,
        les onglets de salon de discussion, les boutons de déconnexion et de
        changement de thème, ainsi que la liste des membres du salon.

        :param fenetre_interface_client: La fenêtre principale de l'interface.
        :type fenetre_interface_client: QMainWindow
        """

        if not fenetre_interface_client.objectName():

            fenetre_interface_client.setObjectName(u"fenetre_interface_client")

        fenetre_interface_client.setWindowTitle("Serveur de messagerie")
        fenetre_interface_client.setFixedSize(1280, 720)

        # Configuration de la barre de menu
        self.barre_menu = QMenuBar(fenetre_interface_client)
        self.barre_menu.setObjectName(u"barre_menu")
        self.barre_menu.setEnabled(True)
        self.barre_menu.setGeometry(QRect(0, 0, 1280, 22))
        self.barre_menu.setAutoFillBackground(False)
        self.barre_menu.setDefaultUp(False)
        self.barre_menu.setNativeMenuBar(True)
        fenetre_interface_client.setMenuBar(self.barre_menu)

        # Configuration de la barre de statut
        self.barre_statut = QStatusBar(fenetre_interface_client)
        self.barre_statut.setObjectName(u"barre_statut")
        self.barre_statut.setEnabled(True)
        self.barre_statut.setSizeGripEnabled(True)
        fenetre_interface_client.setStatusBar(self.barre_statut)

        # Configuration du widget principal
        self.widget_principal = QWidget(fenetre_interface_client)
        self.widget_principal.setObjectName(u"widget_principal")

        # Configuration des éléments "Messages privés"
        self.label_messages_prives = QLabel(self.widget_principal)
        self.label_messages_prives.setText("MP reçus")
        self.label_messages_prives.setObjectName(u"label_messages_prives")
        self.label_messages_prives.setGeometry(QRect(20, 20, 101, 20))
        self.nombre_messages_prives = QLCDNumber(self.widget_principal)
        self.nombre_messages_prives.setObjectName(u"nombre_messages_prives")
        self.nombre_messages_prives.setGeometry(QRect(130, 20, 71, 23))
        self.liste_messages_prives = QListView(self.widget_principal)
        self.liste_messages_prives.setObjectName(u"liste_messages_prives")
        self.liste_messages_prives.setGeometry(QRect(20, 50, 181, 541))

        # Configuration du séparateur horizontal gauche
        self.separateur_horizontal_gauche = QFrame(self.widget_principal)
        self.separateur_horizontal_gauche.setObjectName(
            u"separateur_horizontal_gauche")
        self.separateur_horizontal_gauche.setGeometry(QRect(50, 600, 121, 20))
        self.separateur_horizontal_gauche.setFrameShape(QFrame.Shape.HLine)
        self.separateur_horizontal_gauche.setFrameShadow(QFrame.Shadow.Sunken)

        # Configuration du bouton Déconnexion
        self.bouton_deconnexion = QPushButton(self.widget_principal)
        self.bouton_deconnexion.setText("Déconnexion")
        self.bouton_deconnexion.setObjectName(u"bouton_deconnexion")
        self.bouton_deconnexion.setGeometry(QRect(50, 620, 121, 41))
        self.bouton_deconnexion.clicked.connect(
            self.deconnexion_et_retour_fenetre_accueil)

        # Configuration du séparateur vertical gauche
        self.separateur_vertical_gauche = QFrame(self.widget_principal)
        self.separateur_vertical_gauche.setObjectName(
            u"separateur_vertical_gauche")
        self.separateur_vertical_gauche.setGeometry(QRect(210, 50, 20, 611))
        self.separateur_vertical_gauche.setFrameShape(QFrame.Shape.VLine)
        self.separateur_vertical_gauche.setFrameShadow(QFrame.Shadow.Sunken)

        # Configuration du widget des onglets
        self.widget_onglets = QTabWidget(self.widget_principal)
        self.widget_onglets.setObjectName(u"widget_onglets")
        self.widget_onglets.setGeometry(QRect(240, 20, 801, 571))
        self.widget_onglets.currentChanged.connect(
            self.mettre_a_jour_liste_membres)

        # Configuration des dimensions pour les blocs de chat
        dimensions_blocs = QSizePolicy(QSizePolicy.Policy.Fixed,
                                       QSizePolicy.Policy.Fixed)
        dimensions_blocs.setHorizontalStretch(0)
        dimensions_blocs.setVerticalStretch(0)

        # Configuration des blocs de chat
        self.chat_general = QListView(self.onglet_general)
        self.chat_general.setObjectName(u"chat_general")
        self.chat_general.setGeometry(QRect(0, 0, 791, 541))
        dimensions_blocs.setHeightForWidth(
            self.chat_general.sizePolicy().hasHeightForWidth())
        self.chat_general.setSizePolicy(dimensions_blocs)
        print("avant chat_general.setModel")
        self.chat_general.setModel(self.modele_chat_general)
        self.chat_blabla = QListView(self.onglet_blabla)
        self.chat_blabla.setObjectName(u"chat_blabla")
        self.chat_blabla.setGeometry(QRect(0, 0, 791, 541))
        dimensions_blocs.setHeightForWidth(
            self.chat_blabla.sizePolicy().hasHeightForWidth())
        self.chat_blabla.setSizePolicy(dimensions_blocs)
        print("avant chat_blabla.setModel")
        self.chat_blabla.setModel(self.modele_chat_blabla)
        self.chat_comptabilite = QListView(self.onglet_comptabilite)
        self.chat_comptabilite.setObjectName(u"chat_comptabilite")
        self.chat_comptabilite.setGeometry(QRect(0, 0, 791, 541))
        dimensions_blocs.setHeightForWidth(
            self.chat_comptabilite.sizePolicy().hasHeightForWidth())
        self.chat_comptabilite.setSizePolicy(dimensions_blocs)
        print("avant chat_comptabilite.setModel")
        self.chat_comptabilite.setModel(self.modele_chat_comptabilite)
        self.chat_informatique = QListView(self.onglet_informatique)
        self.chat_informatique.setObjectName(u"chat_informatique")
        self.chat_informatique.setGeometry(QRect(0, 0, 791, 541))
        dimensions_blocs.setHeightForWidth(
            self.chat_informatique.sizePolicy().hasHeightForWidth())
        self.chat_informatique.setSizePolicy(dimensions_blocs)
        self.chat_informatique.setModel(self.modele_chat_informatique)
        self.chat_marketing = QListView(self.onglet_marketing)
        self.chat_marketing.setObjectName(u"chat_marketing")
        self.chat_marketing.setGeometry(QRect(0, 0, 791, 541))
        dimensions_blocs.setHeightForWidth(
            self.chat_marketing.sizePolicy().hasHeightForWidth())
        self.chat_marketing.setSizePolicy(dimensions_blocs)
        self.chat_marketing.setModel(self.modele_chat_marketing)

        # Configuration du champ de saisie de messages
        self.champ_saisie = QLineEdit(self.widget_principal)
        self.champ_saisie.setObjectName(u"champ_saisie")
        self.champ_saisie.setGeometry(QRect(240, 620, 691, 41))

        # Configuration du bouton Envoyer
        self.bouton_envoyer = QPushButton(self.widget_principal)
        self.bouton_envoyer.setText("Envoyer")
        self.bouton_envoyer.setObjectName(u"bouton_envoyer")
        self.bouton_envoyer.setGeometry(QRect(950, 620, 91, 41))
        self.bouton_envoyer.clicked.connect(self.envoyer_saisie_utilisateur)

        # Configuration du séparateur vertical droit
        self.separateur_vertical_droit = QFrame(self.widget_principal)
        self.separateur_vertical_droit.setObjectName(
            u"separateur_vertical_droit")
        self.separateur_vertical_droit.setGeometry(QRect(1050, 40, 20, 621))
        self.separateur_vertical_droit.setFrameShape(QFrame.Shape.VLine)
        self.separateur_vertical_droit.setFrameShadow(QFrame.Shadow.Sunken)

        # Configuration du label des membres du salon
        self.label_membres_salon = QLabel(self.widget_principal)
        self.label_membres_salon.setText("Membres")
        self.label_membres_salon.setObjectName(u"label_membres_salon")
        self.label_membres_salon.setGeometry(QRect(1080, 20, 101, 20))

        # Configuration de l'affichage du nombre des membres du salon
        self.nombre_membres_salon = QLCDNumber(self.widget_principal)
        self.nombre_membres_salon.setObjectName(u"nombre_membres_salon")
        self.nombre_membres_salon.setGeometry(QRect(1190, 20, 71, 23))

        # Configuration de la liste des membres du salon
        self.liste_membres = QListView(self.widget_principal)
        self.liste_membres.setObjectName(u"liste_membres")
        self.liste_membres.setEnabled(True)
        self.liste_membres.setGeometry(QRect(1080, 50, 181, 541))
        self.liste_membres.doubleClicked.connect(self.double_clic_membre_salon)

        # Configuration du séparateur horizontal droit
        self.separateur_horizontal_droit = QFrame(self.widget_principal)
        self.separateur_horizontal_droit.setObjectName(
            u"separateur_horizontal_droit")
        self.separateur_horizontal_droit.setGeometry(QRect(1110, 600, 121, 20))
        self.separateur_horizontal_droit.setFrameShape(QFrame.Shape.HLine)
        self.separateur_horizontal_droit.setFrameShadow(QFrame.Shadow.Sunken)

        # Configuration du bouton Jour/Nuit
        self.bouton_theme = QPushButton(self.widget_principal)
        self.bouton_theme.setText("Jour/Nuit")
        self.bouton_theme.setObjectName(u"bouton_theme")
        self.bouton_theme.setGeometry(QRect(1110, 620, 121, 41))
        self.bouton_theme.clicked.connect(self.changement_theme)

        fenetre_interface_client.setCentralWidget(self.widget_principal)
        self.widget_onglets.setCurrentIndex(0)
        print("Initialisation des salons...")
        self.initialiser_salons()


def execution_programme():
    """
    Exécute le programme de l'application client.

    Cette méthode initialise l'application Qt, crée l'interface d'accueil,
    affiche la fenêtre principale, établit la connexion aux signaux de
    l'interface client, et lance l'exécution de l'application.
    """

    application = QApplication(sys.argv)
    interface_client = InterfaceAccueil()
    interface_client.show()
    interface_client.client.signal_reponse.connect(
        interface_client.gestion_reponses_serveur)
    sys.exit(application.exec())


if __name__ == '__main__':

    execution_programme()
