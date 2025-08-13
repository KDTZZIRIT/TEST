-- --------------------------------------------------------
-- 호스트:                          52.79.248.3
-- 서버 버전:                        10.11.13-MariaDB-0ubuntu0.24.04.1 - Ubuntu 24.04
-- 서버 OS:                        debian-linux-gnu
-- HeidiSQL 버전:                  12.10.0.7000
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- zzirit_db 데이터베이스 구조 내보내기
DROP DATABASE IF EXISTS `zzirit_db`;
CREATE DATABASE IF NOT EXISTS `zzirit_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;
USE `zzirit_db`;

-- 테이블 zzirit_db.pcb_parts 구조 내보내기
DROP TABLE IF EXISTS `pcb_parts`;
CREATE TABLE IF NOT EXISTS `pcb_parts` (
  `part_id` int(11) NOT NULL AUTO_INCREMENT,
  `part_number` varchar(500) DEFAULT NULL,
  `category` varchar(500) DEFAULT NULL,
  `size` varchar(500) DEFAULT NULL,
  `received_date` date DEFAULT NULL,
  `is_humidity_sensitive` tinyint(1) DEFAULT NULL,
  `needs_humidity_control` tinyint(1) DEFAULT NULL,
  `manufacturer` varchar(500) DEFAULT NULL,
  `quantity` int(11) DEFAULT NULL,
  `min_stock` int(11) DEFAULT NULL,
  PRIMARY KEY (`part_id`)
) ENGINE=InnoDB AUTO_INCREMENT=163 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 테이블 데이터 zzirit_db.pcb_parts:~146 rows (대략적) 내보내기
DELETE FROM `pcb_parts`;
INSERT INTO `pcb_parts` (`part_id`, `part_number`, `category`, `size`, `received_date`, `is_humidity_sensitive`, `needs_humidity_control`, `manufacturer`, `quantity`, `min_stock`) VALUES
	(1, 'CL02A104KQ2NNNC', 'Capacitor', '0604', '2025-07-16', 0, 0, 'murata', 10000, 10000),
	(2, 'CL02B101KP2NNNC', 'Capacitor', '1008', '2025-07-16', 0, 0, 'murata', 10000, 1000),
	(3, 'CL02B102KP2NNNC', 'Capacitor', '1008', '2025-06-30', 0, 0, 'samsung', 10000, 74),
	(4, 'CL02B121KP2NNNC', 'Capacitor', '0402', '2025-07-03', 0, 0, 'samsung', 10000, 68),
	(5, 'CL02C330JO2ANNC', 'Capacitor', '0402', '2025-07-01', 0, 0, 'samsung', 10000, 74),
	(6, 'CL02C470JO2ANNC', 'Capacitor', '0402', '2025-07-04', 0, 0, 'samsung', 10000, 84),
	(7, 'CL03A104KA3NNNC', 'Capacitor', '1008', '2025-07-10', 0, 0, 'murata', 10000, 86),
	(8, 'CL03A104KP3NNNC', 'Capacitor', '1008', '2025-07-15', 0, 0, 'samsung', 10000, 64),
	(9, 'CL03A105MO3NRNC', 'Capacitor', '0402', '2025-07-09', 0, 0, 'murata', 9860, 10000),
	(10, 'CL03A105MP3NSNC', 'Capacitor', '1008', '2025-07-07', 0, 0, 'samsung', 10000, 64),
	(11, 'CL03A105MQ3CSNH', 'Capacitor', '1008', '2025-07-04', 0, 0, 'murata', 10000, 86),
	(12, 'CL03A225MP3CRNC', 'Capacitor', '0402', '2025-07-14', 0, 0, 'samsung', 9860, 62),
	(13, 'CL03A225MP3CRND', 'Capacitor', '1008', '2025-07-01', 0, 0, 'samsung', 10000, 66),
	(14, 'CL03A225MQ3CRNC', 'Capacitor', '0604', '2025-07-07', 0, 0, 'murata', 10000, 86),
	(15, 'CL03A473KP3NNNC', 'Capacitor', '0604', '2025-07-13', 0, 0, 'samsung', 10000, 62),
	(16, 'CL03B103KP3NNNC', 'Capacitor', '0604', '2025-07-07', 0, 0, 'samsung', 10000, 82),
	(17, 'CL03C010BA3GNNC', 'Capacitor', '1008', '2025-07-01', 0, 0, 'murata', 10000, 60),
	(18, 'CL03C1R5CA3GNNC', 'Capacitor', '0604', '2025-07-10', 0, 0, 'murata', 10000, 70),
	(19, 'CL03C6R8BA3GNNC', 'Capacitor', '1008', '2025-07-14', 0, 0, 'samsung', 10000, 58),
	(20, 'CL03C8R2BA3GNNC', 'Capacitor', '0402', '2025-06-30', 0, 0, 'samsung', 10000, 88),
	(21, 'CL05A106MP5Z64C', 'Capacitor', '0604', '2025-07-10', 0, 0, 'murata', 10000, 62),
	(22, 'CL05A475KP5ZRNC', 'Capacitor', '0604', '2025-07-04', 0, 0, 'murata', 9860, 66),
	(23, 'CL10A106MAAIZNC', 'Capacitor', '0402', '2025-07-02', 0, 0, 'samsung', 10000, 58),
	(24, 'CLH0603T-56NJ-F', 'Capacitor', '1008', '2025-07-11', 0, 0, 'samsung', 10000, 60),
	(25, 'CM03CG100J25AH', 'Capacitor', '1008', '2025-07-07', 0, 0, 'murata', 10000, 62),
	(26, 'CM03X5R225M10AN-SAT2', 'Capacitor', '0604', '2025-07-12', 0, 0, 'samsung', 10000, 68),
	(27, 'CV03X5R224K06AH', 'Capacitor', '1008', '2025-07-03', 0, 0, 'samsung', 10000, 80),
	(28, 'CV05X5R475M06AH', 'Capacitor', '1008', '2025-07-03', 0, 0, 'samsung', 10000, 94),
	(29, 'DIO6155CL6', 'Capacitor', '1008', '2025-07-05', 0, 0, 'samsung', 10000, 70),
	(30, 'GRM0225C1C1R0BA11', 'Capacitor', '1008', '2025-07-18', 0, 0, 'samsung', 10000, 108),
	(31, 'GRM0225C1C3R9CA11', 'Capacitor', '1008', '2025-07-10', 0, 0, 'samsung', 10000, 76),
	(32, 'GRM0225C1CR50BA11', 'Capacitor', '0402', '2025-07-13', 1, 0, 'samsung', 10000, 88),
	(33, 'GRM0335C1E180J', 'Capacitor', '1008', '2025-07-12', 0, 0, 'murata', 10000, 56),
	(34, 'GRM0335C1E3R9B', 'Capacitor', '1008', '2025-07-15', 0, 0, 'samsung', 10000, 54),
	(35, 'GRM0335C1E470JD01D', 'Capacitor', '0604', '2025-07-14', 0, 0, 'samsung', 10000, 58),
	(36, 'GRM0335C1E4R7C', 'Capacitor', '0604', '2025-07-05', 0, 0, 'samsung', 10000, 62),
	(37, 'GRM0335C1E5R6CD01D', 'Capacitor', '0604', '2025-07-07', 0, 0, 'murata', 10000, 82),
	(38, 'GRM0335C1E820JD01D', 'Capacitor', '0604', '2025-07-05', 0, 0, 'murata', 10000, 66),
	(39, 'GRM0335C1ER50B', 'Capacitor', '1008', '2025-07-19', 0, 0, 'samsung', 10000, 64),
	(40, 'GRM033R60J104KJ', 'Capacitor', '1008', '2025-07-11', 0, 0, 'murata', 10000, 82),
	(41, 'GRM033R60J333K', 'Capacitor', '0402', '2025-07-14', 0, 0, 'murata', 10000, 58),
	(42, 'GRM033R60J474KE90', 'Capacitor', '0402', '2025-07-11', 0, 0, 'samsung', 10000, 74),
	(43, 'GRM033R71C151KD01D', 'Capacitor', '1008', '2025-07-19', 0, 0, 'samsung', 10000, 68),
	(44, 'GRM033R71E102K', 'Capacitor', '0604', '2025-07-11', 1, 0, 'murata', 10000, 62),
	(45, 'GRM033R71E331KA01D', 'Capacitor', '0402', '2025-07-09', 0, 0, 'samsung', 10000, 70),
	(46, 'GRMJN6R61C106M', 'Capacitor', '0402', '2025-07-07', 0, 0, 'samsung', 10000, 90),
	(47, 'GRMJR6R61A106ME01', 'Capacitor', '0604', '2025-07-10', 0, 0, 'samsung', 9860, 84),
	(48, 'UCLAMP3321ZA', 'Capacitor', '1008', '2025-07-06', 0, 0, 'samsung', 10000, 80),
	(49, 'PESD5V0V1BDSF', 'Diode', '0604', '2025-06-30', 0, 0, 'murata', 10000, 222),
	(50, 'PMEG3005ELD', 'Diode', '0604', '2025-07-10', 0, 0, 'murata', 10000, 10000),
	(51, 'BLM03AX121SN1D', 'Ferrite Bead', '0604', '2025-07-08', 0, 0, 'murata', 10000, 60),
	(52, 'BLM03AX601SN1D', 'Ferrite Bead', '0402', '2025-07-12', 0, 0, 'samsung', 10000, 10000),
	(53, 'BLM03PX220SN1D', 'Ferrite Bead', '0402', '2025-07-04', 0, 0, 'murata', 10000, 70),
	(54, 'BLM03PX800SN1D', 'Ferrite Bead', '0604', '2025-06-30', 0, 0, 'murata', 10000, 58),
	(55, 'BLM15EX121SN1D', 'Ferrite Bead', '0402', '2025-07-09', 0, 0, 'murata', 10000, 60),
	(56, 'BLM15PX330SN1', 'Ferrite Bead', '0604', '2025-07-08', 0, 0, 'samsung', 10000, 60),
	(57, 'BK13S06-40DS/2-0.35V', 'Inductor', '0402', '2025-07-15', 0, 0, 'murata', 10000, 44),
	(58, 'BK73B06-50DS2-0.3V', 'Inductor', '0604', '2025-07-19', 0, 0, 'samsung', 10000, 1),
	(59, 'CIGT2016R6TMR47SLE', 'Inductor', '1008', '2025-07-13', 0, 0, 'murata', 10000, 10000),
	(60, 'CIGT2520R6TL2R2SLE', 'Inductor', '1008', '2025-07-05', 0, 0, 'samsung', 10000, 50),
	(61, 'CIGT2520R6TL6R8SLE', 'Inductor', '1008', '2025-07-02', 0, 0, 'samsung', 10000, 52),
	(62, 'LQP02HQ0N6B02E', 'Inductor', '1008', '2025-07-13', 0, 0, 'samsung', 10000, 52),
	(63, 'LQP02HQ10NJ02E', 'Inductor', '0402', '2025-07-06', 0, 0, 'murata', 10000, 56),
	(64, 'LQP02HQ12NJ02E', 'Inductor', '0402', '2025-07-17', 0, 0, 'samsung', 10000, 44),
	(65, 'LQP02HQ18NJ02E', 'Inductor', '1008', '2025-07-10', 1, 0, 'samsung', 10000, 44),
	(66, 'LQP02HQ1N0B02E', 'Inductor', '1008', '2025-07-17', 0, 0, 'samsung', 10000, 60),
	(67, 'LQP02HQ1N2B02E', 'Inductor', '1008', '2025-06-30', 0, 0, 'samsung', 10000, 46),
	(68, 'LQP02HQ1N5B02E', 'Inductor', '0402', '2025-07-03', 0, 0, 'murata', 10000, 44),
	(69, 'LQP02HQ1N8B02E', 'Inductor', '1008', '2025-07-09', 0, 0, 'murata', 10000, 42),
	(70, 'LQP02HQ22NH02E', 'Inductor', '0402', '2025-07-08', 0, 0, 'samsung', 10000, 58),
	(71, 'LQP02HQ2N2B02E', 'Inductor', '1008', '2025-07-12', 0, 0, 'samsung', 10000, 42),
	(72, 'LQP02HQ2N4B02E', 'Inductor', '0604', '2025-07-11', 0, 0, 'samsung', 10000, 48),
	(73, 'LQP02HQ2N7B02E', 'Inductor', '0604', '2025-07-19', 0, 0, 'murata', 10000, 46),
	(74, 'LQP02HQ3N3B02E', 'Inductor', '0402', '2025-07-11', 0, 0, 'samsung', 10000, 46),
	(75, 'LQP02HQ3N9B02E', 'Inductor', '0402', '2025-07-12', 0, 0, 'samsung', 10000, 44),
	(76, 'LQP02HQ6N8J02E', 'Inductor', '0604', '2025-07-13', 0, 0, 'murata', 10000, 46),
	(77, 'LQP03TG15NJ02D', 'Inductor', '0402', '2025-07-06', 0, 0, 'samsung', 10000, 48),
	(78, 'LQP03TG6N8J02D', 'Inductor', '1008', '2025-07-07', 1, 0, 'murata', 10000, 44),
	(79, 'LQP03TG8N2J02D', 'Inductor', '0402', '2025-07-05', 0, 0, 'murata', 10000, 48),
	(80, 'LQP03TN0N6B02D', 'Inductor', '0402', '2025-07-08', 0, 0, 'samsung', 10000, 50),
	(81, 'LQP03TN10NH02D', 'Inductor', '0604', '2025-07-16', 0, 0, 'murata', 10000, 42),
	(82, 'LQP03TN12NJ02D', 'Inductor', '0604', '2025-07-10', 0, 0, 'samsung', 10000, 50),
	(83, 'LQP03TN1N2B02D', 'Inductor', '0604', '2025-07-09', 0, 0, 'samsung', 10000, 50),
	(84, 'LQP03TN1N5B02D', 'Inductor', '0402', '2025-07-16', 0, 0, 'samsung', 10000, 52),
	(85, 'LQP03TN1N8B02D', 'Inductor', '0604', '2025-07-07', 0, 0, 'samsung', 10000, 50),
	(86, 'LQP03TN22NJ02D', 'Inductor', '0604', '2025-06-29', 0, 0, 'samsung', 10000, 42),
	(87, 'LQP03TN2N2B02D', 'Inductor', '0402', '2025-07-13', 0, 0, 'murata', 10000, 52),
	(88, 'LQP03TN3N3B02D', 'Inductor', '0402', '2025-07-10', 0, 0, 'murata', 10000, 62),
	(89, 'LQP03TN3N6B02D', 'Inductor', '0604', '2025-07-16', 0, 0, 'murata', 10000, 50),
	(90, 'LQP03TN3N9B02D', 'Inductor', '1008', '2025-07-10', 0, 0, 'murata', 10000, 48),
	(91, 'LQP03TN47NJ02D', 'Inductor', '0402', '2025-07-12', 0, 0, 'murata', 10000, 44),
	(92, 'LQP03TN4N3J02D', 'Inductor', '1008', '2025-07-15', 0, 0, 'samsung', 10000, 50),
	(93, 'LQP03TN4N7H02D', 'Inductor', '1008', '2025-07-05', 0, 0, 'murata', 10000, 48),
	(94, 'LQP03TN5N6J02D', 'Inductor', '0402', '2025-06-29', 0, 0, 'samsung', 10000, 46),
	(95, 'LQP03TN68NJ02', 'Inductor', '0604', '2025-07-02', 0, 0, 'murata', 10000, 54),
	(96, 'LQP03TN6N2J02D', 'Inductor', '0604', '2025-07-02', 0, 0, 'murata', 10000, 50),
	(97, 'LFD211G44PK9F557', 'Misc IC / Unknown', '2015', '2025-07-15', 1, 1, 'samsung', 10000, 122),
	(98, 'LST03-8P-H06-E20000', 'Misc IC / Unknown', '2015', '2025-07-04', 1, 1, 'murata', 10000, 10000),
	(99, 'SAFFW1G54AA0E3K', 'Misc IC / Unknown', '2015', '2025-07-06', 1, 1, 'murata', 10000, 140),
	(100, 'AOCR33135A', 'PMIC / Power IC', '2520', '2025-07-18', 1, 1, 'murata', 10000, 96),
	(101, 'ET3138SE', 'PMIC / Power IC', '2520', '2025-06-30', 0, 1, 'murata', 10000, 114),
	(102, 'ET53128YB', 'PMIC / Power IC', '2520', '2025-07-02', 1, 1, 'murata', 10000, 84),
	(103, 'MAX17333X22+T', 'PMIC / Power IC', '2015', '2025-07-01', 1, 1, 'murata', 10000, 10000),
	(104, 'MXD8546CDS', 'PMIC / Power IC', '2520', '2025-07-11', 1, 1, 'samsung', 10000, 76),
	(105, 'MXDLN14TS', 'PMIC / Power IC', '2015', '2025-07-17', 1, 1, 'murata', 10000, 94),
	(106, 'S2DOS15A01-6032', 'PMIC / Power IC', '2520', '2025-07-02', 1, 1, 'murata', 10000, 60),
	(107, 'SM3012A', 'PMIC / Power IC', '2015', '2025-06-30', 1, 1, 'murata', 10000, 86),
	(108, 'QM23030', 'RF Filter / Duplexer', '2520', '2025-07-13', 1, 1, 'samsung', 10000, 84),
	(109, 'QM42500A', 'RF Filter / Duplexer', '2015', '2025-07-07', 1, 1, 'samsung', 10000, 56),
	(110, 'SAYRZ634MBA0C3K', 'RF Filter / Duplexer', '2520', '2025-07-09', 1, 1, 'murata', 10000, 66),
	(111, 'SAYRZ725MBA0L3K', 'RF Filter / Duplexer', '2015', '2025-07-03', 0, 1, 'murata', 10000, 10000),
	(112, 'SFHG76AF302', 'RF Filter / Duplexer', '2520', '2025-07-04', 1, 1, 'samsung', 10000, 60),
	(113, 'SFHG89BF302', 'RF Filter / Duplexer', '2015', '2025-07-12', 1, 1, 'murata', 10000, 72),
	(114, 'SFML5Y0J001', 'RF Filter / Duplexer', '2015', '2025-07-04', 0, 1, 'samsung', 10000, 82),
	(115, 'SFML7F0J001', 'RF Filter / Duplexer', '2015', '2025-07-15', 0, 1, 'samsung', 10000, 58),
	(116, 'SFWG76ME602', 'RF Filter / Duplexer', '2520', '2025-06-30', 1, 1, 'murata', 10000, 56),
	(117, 'SFH722FF302', 'RF Filter / Module', '2015', '2025-07-14', 1, 1, 'samsung', 10000, 1),
	(118, 'QPM7815A', 'RF Front-End / PA', '2520', '2025-07-01', 1, 1, 'murata', 10000, 68),
	(119, 'SKY58093-11', 'RF Front-End / PA', '2520', '2025-07-11', 0, 1, 'murata', 10000, 92),
	(120, 'SKY58098-11', 'RF Front-End / PA', '2015', '2025-07-12', 0, 1, 'samsung', 10000, 10000),
	(121, 'SKY58261-11', 'RF Front-End / PA', '2015', '2025-06-29', 1, 1, 'murata', 10000, 94),
	(122, 'ERJ1GEJ0R00C', 'Resistor', '0402', '2025-07-10', 0, 0, 'samsung', 10000, 92),
	(123, 'ERJ1GEJ102C', 'Resistor', '0604', '2025-07-08', 0, 0, 'samsung', 9860, 108),
	(124, 'ERJ1GENJ472X', 'Resistor', '0604', '2025-07-05', 0, 0, 'samsung', 10000, 10000),
	(125, 'MCR006MZPF1503', 'Resistor', '0402', '2025-07-02', 0, 0, 'murata', 10000, 76),
	(126, 'MCR006YZPF1003', 'Resistor', '0604', '2025-07-08', 0, 0, 'murata', 10000, 92),
	(127, 'MCR006YZPF6800', 'Resistor', '0604', '2025-07-10', 0, 0, 'samsung', 10000, 106),
	(128, 'MCR006YZPJ200', 'Resistor', '1008', '2025-07-05', 0, 0, 'murata', 10000, 88),
	(129, 'MCR006YZPJ222', 'Resistor', '0402', '2025-06-30', 0, 0, 'samsung', 10000, 132),
	(130, 'MCR006YZPJ300', 'Resistor', '0402', '2025-07-13', 0, 0, 'samsung', 10000, 112),
	(131, 'RC0201FR-071ML', 'Resistor', '0402', '2025-07-06', 0, 0, 'murata', 10000, 124),
	(132, 'RC0201FR-07470KL', 'Resistor', '0402', '2025-07-11', 0, 0, 'murata', 10000, 86),
	(133, 'RC00402F103CS', 'Resistor', '1008', '2025-06-30', 0, 0, 'murata', 10000, 94),
	(134, 'RC00402F104CS', 'Resistor', '1008', '2025-07-08', 0, 0, 'samsung', 10000, 98),
	(135, 'RC00402F204CS', 'Resistor', '1008', '2025-07-14', 0, 0, 'samsung', 10000, 114),
	(136, 'RC00402J102CS', 'Resistor', '0402', '2025-07-04', 0, 0, 'murata', 9860, 110),
	(137, 'RC00402J103CS', 'Resistor', '0402', '2025-07-04', 0, 0, 'murata', 10000, 76),
	(138, 'RC00402J222CS', 'Resistor', '0402', '2025-07-13', 0, 0, 'samsung', 10000, 102),
	(139, 'RC00402J472CS', 'Resistor', '0402', '2025-07-07', 0, 0, 'murata', 10000, 78),
	(140, 'RC0603J220CS', 'Resistor', '0604', '2025-07-03', 0, 0, 'murata', 10000, 88),
	(141, 'RC0603J2R2CS', 'Resistor', '1008', '2025-07-03', 0, 0, 'murata', 10000, 102),
	(142, 'RC0603J510CS', 'Resistor', '1008', '2025-07-10', 0, 0, 'murata', 9860, 106),
	(143, 'RC1005F104CS', 'Resistor', '1008', '2025-07-04', 0, 0, 'murata', 10000, 76),
	(144, 'RC1005F204CS', 'Resistor', '0604', '2025-07-01', 1, 0, 'murata', 10000, 104),
	(145, 'RC1005F2403CS', 'Resistor', '0604', '2025-07-08', 0, 0, 'murata', 9720, 116),
	(146, 'RM02FTN6200', 'Resistor', '1008', '2025-07-14', 0, 0, 'samsung', 10000, 108);

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
