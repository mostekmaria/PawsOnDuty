-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Paź 14, 2024 at 08:21 PM
-- Wersja serwera: 10.4.32-MariaDB
-- Wersja PHP: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `crimedb`
--

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `event_features`
--

CREATE TABLE `event_features` (
  `event_feature_id` smallint(6) NOT NULL,
  `report_id` smallint(6) NOT NULL,
  `event_description` text DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `event_time` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `event_features`
--

INSERT INTO `event_features` (`event_feature_id`, `report_id`, `event_description`, `address`, `event_time`) VALUES
(1, 1, 'Załoga G baluje na naszym osiedlu. Nie wiem jak ich powstrzymać.', 'Janusza Supniewskiego 15 Kraków Województwo małopolskie 31-527', '2024-10-09 12:55');

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `perpetrators`
--

CREATE TABLE `perpetrators` (
  `perpetrator_id` smallint(6) NOT NULL,
  `event_feature_id` smallint(6) NOT NULL,
  `appearance` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `perpetrators`
--

INSERT INTO `perpetrators` (`perpetrator_id`, `event_feature_id`, `appearance`) VALUES
(1, 1, '1 - Paskudny facet');

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `reports`
--

CREATE TABLE `reports` (
  `report_id` smallint(6) NOT NULL,
  `title` varchar(100) DEFAULT NULL,
  `user_id` int(6) DEFAULT NULL,
  `report_time` varchar(20) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `reports`
--

INSERT INTO `reports` (`report_id`, `title`, `user_id`, `report_time`, `status`) VALUES
(1, 'Załoga G baluje na naszym osie...', 2, '2024-10-14 10:55:44', 'zindentyfikowano');

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `suspects`
--

CREATE TABLE `suspects` (
  `suspect_id` smallint(6) NOT NULL,
  `report_id` smallint(6) NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `surname` varchar(50) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `birthdate` date DEFAULT NULL,
  `photo` mediumblob DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--


-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `users`
--

CREATE TABLE `users` (
  `user_id` int(6) NOT NULL,
  `login` varchar(50) DEFAULT NULL,
  `password` varchar(255) NOT NULL CHECK (octet_length(`password`) >= 6),
  `role` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `name` varchar(50) DEFAULT NULL,
  `surname` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `login`, `password`, `role`, `email`, `name`, `surname`) VALUES
(1, 'funkcjonariusz1', 'abe31fe1a2113e7e8bf174164515802806d388cf4f394cceace7341a182271ab', 'funkcjonariusz', 'anetk@it.pl', 'Adam', 'Malysz'),
(2, 'antoni', 'abe31fe1a2113e7e8bf174164515802806d388cf4f394cceace7341a182271ab', 'cywil', 'marian.pazdzioch@onet.pl', 'Tomek', 'Atomek');

-- --------------------------------------------------------

--
-- Struktura tabeli dla tabeli `witnesses`
--

CREATE TABLE `witnesses` (
  `witness_id` smallint(6) NOT NULL,
  `event_feature_id` smallint(6) NOT NULL,
  `info_contact` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `witnesses`
--

INSERT INTO `witnesses` (`witness_id`, `event_feature_id`, `info_contact`) VALUES
(1, 1, 'anonimowy');

--
-- Indeksy dla zrzutów tabel
--

--
-- Indeksy dla tabeli `event_features`
--
ALTER TABLE `event_features`
  ADD PRIMARY KEY (`event_feature_id`),
  ADD KEY `report_id` (`report_id`);

--
-- Indeksy dla tabeli `perpetrators`
--
ALTER TABLE `perpetrators`
  ADD PRIMARY KEY (`perpetrator_id`),
  ADD KEY `event_feature_id` (`event_feature_id`);

--
-- Indeksy dla tabeli `reports`
--
ALTER TABLE `reports`
  ADD PRIMARY KEY (`report_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeksy dla tabeli `suspects`
--
ALTER TABLE `suspects`
  ADD PRIMARY KEY (`suspect_id`),
  ADD KEY `event_feature_id` (`report_id`);

--
-- Indeksy dla tabeli `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`);

--
-- Indeksy dla tabeli `witnesses`
--
ALTER TABLE `witnesses`
  ADD PRIMARY KEY (`witness_id`),
  ADD KEY `event_feature_id` (`event_feature_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `event_features`
--
ALTER TABLE `event_features`
  MODIFY `event_feature_id` smallint(6) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `perpetrators`
--
ALTER TABLE `perpetrators`
  MODIFY `perpetrator_id` smallint(6) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `reports`
--
ALTER TABLE `reports`
  MODIFY `report_id` smallint(6) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `suspects`
--
ALTER TABLE `suspects`
  MODIFY `suspect_id` smallint(6) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(6) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `witnesses`
--
ALTER TABLE `witnesses`
  MODIFY `witness_id` smallint(6) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `event_features`
--
ALTER TABLE `event_features`
  ADD CONSTRAINT `event_features_ibfk_1` FOREIGN KEY (`report_id`) REFERENCES `reports` (`report_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `perpetrators`
--
ALTER TABLE `perpetrators`
  ADD CONSTRAINT `perpetrators_ibfk_1` FOREIGN KEY (`event_feature_id`) REFERENCES `event_features` (`event_feature_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `reports`
--
ALTER TABLE `reports`
  ADD CONSTRAINT `reports_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL ON UPDATE CASCADE;

--
-- Constraints for table `suspects`
--
ALTER TABLE `suspects`
  ADD CONSTRAINT `suspects_ibfk_1` FOREIGN KEY (`report_id`) REFERENCES `event_features` (`event_feature_id`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Constraints for table `witnesses`
--
ALTER TABLE `witnesses`
  ADD CONSTRAINT `witnesses_ibfk_1` FOREIGN KEY (`event_feature_id`) REFERENCES `event_features` (`event_feature_id`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
