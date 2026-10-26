CREATE TABLE IF NOT EXISTS `unifist`.`clash` (
  `id` VARCHAR(255) COLLATE utf8mb4_bin NOT NULL,
  `what` JSON NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `unifist`.`journal` (
  `id` VARCHAR(255) COLLATE utf8mb4_bin NOT NULL,
  `resource_id` VARCHAR(255) NOT NULL,
  `when` BIGINT NOT NULL,
  `what` JSON NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `resource_id` (`resource_id`)
);

CREATE TABLE IF NOT EXISTS `unifist`.`route` (
  `id` BIGINT AUTO_INCREMENT,
  `identifier` VARCHAR(255) NOT NULL DEFAULT '',
  `model` VARCHAR(255) NOT NULL DEFAULT '',
  `source` VARCHAR(255) NOT NULL DEFAULT '',
  `unum` VARCHAR(255) NOT NULL DEFAULT '',
  `role` VARCHAR(255) NOT NULL DEFAULT 'owner',
  `holder` VARCHAR(255) NOT NULL,
  `url` VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE `identifier_model_source_unum_role_holder` (`identifier`,`model`,`source`,`unum`,`role`,`holder`)
);

CREATE TABLE IF NOT EXISTS `unifist`.`scribe` (
  `id` BIGINT AUTO_INCREMENT,
  `identifier` VARCHAR(255) NOT NULL DEFAULT '',
  `model` VARCHAR(255) NOT NULL DEFAULT '',
  `source` VARCHAR(255) NOT NULL DEFAULT '',
  `unum` VARCHAR(255) NOT NULL DEFAULT '',
  `to` VARCHAR(255) NOT NULL DEFAULT 'owner',
  PRIMARY KEY (`id`),
  UNIQUE `identifier_model_source_unum` (`identifier`,`model`,`source`,`unum`)
);

CREATE TABLE IF NOT EXISTS `unifist`.`sequence` (
  `id` BIGINT AUTO_INCREMENT,
  `unum` VARCHAR(255) NOT NULL,
  `source` VARCHAR(255) NOT NULL,
  `model` VARCHAR(255) NOT NULL,
  `current` BIGINT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE `unum_source_model` (`unum`,`source`,`model`)
);

CREATE TABLE IF NOT EXISTS `unifist`.`slug` (
  `id` BIGINT AUTO_INCREMENT,
  `unum` VARCHAR(255) NOT NULL,
  `source` VARCHAR(255) NOT NULL,
  `model` VARCHAR(255) NOT NULL,
  `current` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE `unum_source_model_current` (`unum`,`source`,`model`,`current`)
);
