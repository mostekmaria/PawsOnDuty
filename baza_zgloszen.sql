-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 05, 2024 at 07:11 PM
-- Wersja serwera: 10.4.32-MariaDB
-- Wersja PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `baza_zgloszen`
--

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `event_features`
--

CREATE TABLE `event_features` (
  `event_feature_id` smallint(6) NOT NULL,
  `perp_id` smallint(6) DEFAULT NULL,
  `event_desc` text DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `event_time` varchar(50) DEFAULT NULL,
  `witness_id` smallint(6) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `perpetrators`
--

CREATE TABLE `perpetrators` (
  `perp_id` smallint(6) NOT NULL,
  `appearance` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `reports`
--

CREATE TABLE `reports` (
  `report_id` smallint(6) NOT NULL,
  `title` varchar(100) DEFAULT NULL,
  `user_id` smallint(6) DEFAULT NULL,
  `rep_time` time DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `event_feature_id` smallint(6) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `suspects`
--

CREATE TABLE `suspects` (
  `susp_id` smallint(6) NOT NULL,
  `perp_id` smallint(6) DEFAULT NULL,
  `name` varchar(50) DEFAULT NULL,
  `surname` varchar(50) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `birthdate` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `users`
--

CREATE TABLE `users` (
  `user_id` smallint(6) NOT NULL,
  `login` varchar(50) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `name` varchar(50) DEFAULT NULL,
  `surname` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `witnesses`
--

CREATE TABLE `witnesses` (
  `witness_id` smallint(6) NOT NULL,
  `info_contact` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Indeksy dla zrzutów tabel
--

--
-- Indeksy dla tabeli `event_features`
--
ALTER TABLE `event_features`
  ADD PRIMARY KEY (`event_feature_id`),
  ADD KEY `perp_id` (`perp_id`),
  ADD KEY `witness_id` (`witness_id`);

--
-- Indeksy dla tabeli `perpetrators`
--
ALTER TABLE `perpetrators`
  ADD PRIMARY KEY (`perp_id`);

--
-- Indeksy dla tabeli `reports`
--
ALTER TABLE `reports`
  ADD PRIMARY KEY (`report_id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `event_feature_id` (`event_feature_id`);

--
-- Indeksy dla tabeli `suspects`
--
ALTER TABLE `suspects`
  ADD PRIMARY KEY (`susp_id`),
  ADD KEY `perp_id` (`perp_id`);

--
-- Indeksy dla tabeli `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`);

--
-- Indeksy dla tabeli `witnesses`
--
ALTER TABLE `witnesses`
  ADD PRIMARY KEY (`witness_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `event_features`
--
ALTER TABLE `event_features`
  MODIFY `event_feature_id` smallint(6) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `perpetrators`
--
ALTER TABLE `perpetrators`
  MODIFY `perp_id` smallint(6) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `reports`
--
ALTER TABLE `reports`
  MODIFY `report_id` smallint(6) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `suspects`
--
ALTER TABLE `suspects`
  MODIFY `susp_id` smallint(6) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` smallint(6) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `witnesses`
--
ALTER TABLE `witnesses`
  MODIFY `witness_id` smallint(6) NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `event_features`
--
ALTER TABLE `event_features`
  ADD CONSTRAINT `event_features_ibfk_1` FOREIGN KEY (`perp_id`) REFERENCES `perpetrators` (`perp_id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `event_features_ibfk_2` FOREIGN KEY (`witness_id`) REFERENCES `witnesses` (`witness_id`) ON UPDATE CASCADE;

--
-- Constraints for table `reports`
--
ALTER TABLE `reports`
  ADD CONSTRAINT `reports_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  ADD CONSTRAINT `reports_ibfk_2` FOREIGN KEY (`event_feature_id`) REFERENCES `event_features` (`event_feature_id`);

--
-- Constraints for table `suspects`
--
ALTER TABLE `suspects`
  ADD CONSTRAINT `suspects_ibfk_1` FOREIGN KEY (`perp_id`) REFERENCES `perpetrators` (`perp_id`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
