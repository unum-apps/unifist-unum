CREATE TABLE IF NOT EXISTS `unum`.`clash` (
  `id` VARCHAR(255) COLLATE utf8mb4_bin NOT NULL,
  `what` JSON NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `unum`.`route` (
  `id` BIGINT AUTO_INCREMENT,
  `identifier` VARCHAR(255) NOT NULL DEFAULT '',
  `model` VARCHAR(64) NOT NULL DEFAULT '',
  `source` VARCHAR(64) NOT NULL DEFAULT '',
  `unum` VARCHAR(64) NOT NULL DEFAULT '',
  `role` VARCHAR(64) NOT NULL DEFAULT 'owner',
  `holder` VARCHAR(64) NOT NULL,
  `url` VARCHAR(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  UNIQUE `identifier_model_source_unum_role_holder` (`identifier`,`model`,`source`,`unum`,`role`,`holder`)
);

CREATE TABLE IF NOT EXISTS `unum`.`scribe` (
  `id` BIGINT AUTO_INCREMENT,
  `identifier` VARCHAR(255) NOT NULL DEFAULT '',
  `model` VARCHAR(64) NOT NULL DEFAULT '',
  `source` VARCHAR(64) NOT NULL DEFAULT '',
  `unum` VARCHAR(64) NOT NULL DEFAULT '',
  `to` VARCHAR(255) NOT NULL DEFAULT 'owner',
  PRIMARY KEY (`id`),
  UNIQUE `identifier_model_source_unum` (`identifier`,`model`,`source`,`unum`)
);
