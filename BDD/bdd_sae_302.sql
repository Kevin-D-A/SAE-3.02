-- MySQL dump 10.13  Distrib 8.0.33, for Win64 (x86_64)
--
-- Host: localhost    Database: sae_302
-- ------------------------------------------------------
-- Server version	8.0.33

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `clients`
--

DROP TABLE IF EXISTS `clients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `clients` (
  `id_client` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) NOT NULL,
  `prenom` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `mot_de_passe` varchar(255) NOT NULL,
  `permission` varchar(255) NOT NULL,
  PRIMARY KEY (`id_client`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clients`
--

LOCK TABLES `clients` WRITE;
/*!40000 ALTER TABLE `clients` DISABLE KEYS */;
INSERT INTO `clients` VALUES (1,'admin','admin','admin@admin.com','admin','administrateur');
/*!40000 ALTER TABLE `clients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `historique_ip`
--

DROP TABLE IF EXISTS `historique_ip`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historique_ip` (
  `id_historique` int NOT NULL AUTO_INCREMENT,
  `ip_client` varchar(16) NOT NULL,
  `email_client` varchar(255) NOT NULL,
  `horodatage_connexion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_historique`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historique_ip`
--

LOCK TABLES `historique_ip` WRITE;
/*!40000 ALTER TABLE `historique_ip` DISABLE KEYS */;
/*!40000 ALTER TABLE `historique_ip` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `membres_salons_publics`
--

DROP TABLE IF EXISTS `membres_salons_publics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `membres_salons_publics` (
  `id_membre` int NOT NULL AUTO_INCREMENT,
  `id_client` int NOT NULL,
  `id_salon_public` int NOT NULL,
  PRIMARY KEY (`id_membre`),
  KEY `id_client` (`id_client`),
  KEY `id_salon_public` (`id_salon_public`),
  CONSTRAINT `membres_salons_publics_ibfk_1` FOREIGN KEY (`id_client`) REFERENCES `clients` (`id_client`),
  CONSTRAINT `membres_salons_publics_ibfk_2` FOREIGN KEY (`id_salon_public`) REFERENCES `salons_publics` (`id_salon_public`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `membres_salons_publics`
--

LOCK TABLES `membres_salons_publics` WRITE;
/*!40000 ALTER TABLE `membres_salons_publics` DISABLE KEYS */;
/*!40000 ALTER TABLE `membres_salons_publics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `id_message` int NOT NULL AUTO_INCREMENT,
  `id_client` int NOT NULL,
  `contenu` text NOT NULL,
  `horodatage` datetime NOT NULL,
  `id_salon_public` int DEFAULT NULL,
  `id_salon_prive` int DEFAULT NULL,
  PRIMARY KEY (`id_message`),
  KEY `id_client` (`id_client`),
  KEY `id_salon_prive` (`id_salon_prive`),
  KEY `id_salon_public` (`id_salon_public`),
  CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`id_client`) REFERENCES `clients` (`id_client`),
  CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`id_salon_prive`) REFERENCES `salons_prives` (`id_salon_prive`),
  CONSTRAINT `messages_ibfk_3` FOREIGN KEY (`id_salon_public`) REFERENCES `salons_publics` (`id_salon_public`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `salons_prives`
--

DROP TABLE IF EXISTS `salons_prives`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `salons_prives` (
  `id_salon_prive` int NOT NULL AUTO_INCREMENT,
  `email_participant_1` varchar(255) NOT NULL,
  `email_participant_2` varchar(255) NOT NULL,
  PRIMARY KEY (`id_salon_prive`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `salons_prives`
--

LOCK TABLES `salons_prives` WRITE;
/*!40000 ALTER TABLE `salons_prives` DISABLE KEYS */;
/*!40000 ALTER TABLE `salons_prives` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `salons_publics`
--

DROP TABLE IF EXISTS `salons_publics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `salons_publics` (
  `id_salon_public` int NOT NULL AUTO_INCREMENT,
  `nom_salon` varchar(255) NOT NULL,
  `description` varchar(255) NOT NULL,
  PRIMARY KEY (`id_salon_public`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `salons_publics`
--

LOCK TABLES `salons_publics` WRITE;
/*!40000 ALTER TABLE `salons_publics` DISABLE KEYS */;
INSERT INTO `salons_publics` VALUES (1,'General','Salon par d├®faut.'),(2,'Blabla','Acc├¿s automatique sur demande.'),(3,'Comptabilite','Acc├¿s sur traitement de la demande.'),(4,'Informatique','Acc├¿s sur traitement de la demande.'),(5,'Marketing','Acc├¿s sur traitement de la demande.');
/*!40000 ALTER TABLE `salons_publics` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sanctions`
--

DROP TABLE IF EXISTS `sanctions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sanctions` (
  `id_sanction` int NOT NULL AUTO_INCREMENT,
  `type_sanction` enum('ban','kick','mute') NOT NULL,
  `duree_sanction` int DEFAULT NULL,
  `motif_sanction` text NOT NULL,
  `ip_client` varchar(16) NOT NULL,
  `email_client` varchar(255) NOT NULL,
  `horodatage_sanction` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_sanction`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sanctions`
--

LOCK TABLES `sanctions` WRITE;
/*!40000 ALTER TABLE `sanctions` DISABLE KEYS */;
/*!40000 ALTER TABLE `sanctions` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-12-31 23:47:51
