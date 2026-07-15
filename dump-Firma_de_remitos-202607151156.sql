-- MySQL dump 10.13  Distrib 8.0.19, for Win64 (x86_64)
--
-- Host: dydb2-instance-1.cz8kik28igwg.us-east-1.rds.amazonaws.com    Database: Firma_de_remitos
-- ------------------------------------------------------
-- Server version	8.0.42

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
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '';

--
-- Table structure for table `remitos`
--

DROP TABLE IF EXISTS `remitos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `remitos` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `finne_transaccionID` int DEFAULT NULL,
  `finne_Copias` tinyint DEFAULT NULL,
  `finne_Fecha` date DEFAULT NULL,
  `finne_CodigoCliente` int DEFAULT NULL,
  `finne_Cliente` varchar(100) DEFAULT NULL,
  `finne_importe_total` decimal(19,4) DEFAULT NULL,
  `finne_Comprobante` varchar(30) DEFAULT NULL,
  `finne_Reclamado` tinyint(1) DEFAULT NULL,
  `finne_FechaUltimoReclamo` date DEFAULT NULL,
  `finne_DocNroInterno` varchar(100) DEFAULT NULL,
  `finne_Descripcion` varchar(255) DEFAULT NULL,
  `finne_cbte_relacionado` varchar(50) DEFAULT NULL,
  `ocr_original` json DEFAULT NULL,
  `ocr_duplicado` json DEFAULT NULL,
  `ocr_triplicado` json DEFAULT NULL,
  `ocr_cuatriplcado` json DEFAULT NULL,
  `bot_confirmado_cliente` tinyint(1) DEFAULT NULL,
  `bot_confirmado_distribuidor` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'Firma_de_remitos'
--
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-07-15 11:56:31
