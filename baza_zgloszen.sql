create database CrimeDB;
begin;

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

CREATE TABLE `users` (
  `user_id` int(6) PRIMARY KEY AUTO_INCREMENT,
  `login` varchar(50) DEFAULT NULL,
  `password` varchar(255) NOT NULL CHECK (LENGTH(password) >= 6),
  `role` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `name` varchar(50) DEFAULT NULL,
  `surname` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `reports` (
  `report_id` smallint(6) PRIMARY KEY AUTO_INCREMENT,
  `title` varchar(100) DEFAULT NULL,
  `user_id` int(6),
  `report_time` time DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`user_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE `event_features` (
  `event_feature_id` smallint(6) PRIMARY KEY AUTO_INCREMENT,
  `report_id` smallint(6) NOT NULL,
  `event_description` text DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `event_time` varchar(50) DEFAULT NULL,
  FOREIGN KEY (`report_id`) REFERENCES `reports`(`report_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `suspects` (
  `suspect_id` smallint(6) PRIMARY KEY AUTO_INCREMENT,
  `event_feature_id` smallint(6) NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `surname` varchar(50) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `birthdate` date DEFAULT NULL,
  FOREIGN KEY (`event_feature_id`) REFERENCES `event_features`(`event_feature_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `witnesses` (
  `witness_id` smallint(6) PRIMARY KEY AUTO_INCREMENT,
  `event_feature_id` smallint(6) NOT NULL,
  `info_contact` text DEFAULT NULL,
  FOREIGN KEY (`event_feature_id`) REFERENCES `event_features`(`event_feature_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;


CREATE TABLE `perpetrators` (
  `perpetrator_id` smallint(6) PRIMARY KEY AUTO_INCREMENT,
  `event_feature_id` smallint(6) NOT NULL,
  `appearance` text DEFAULT NULL,
  FOREIGN KEY (`event_feature_id`) REFERENCES `event_features`(`event_feature_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;