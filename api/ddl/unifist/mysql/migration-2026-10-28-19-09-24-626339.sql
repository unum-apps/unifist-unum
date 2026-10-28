ALTER TABLE `unifist`.`sequence`
  CHANGE `unum` `home` VARCHAR(64) NOT NULL,
  ADD UNIQUE `home_source_model` (`home`,`source`,`model`),
  DROP INDEX `unum_source_model`;

ALTER TABLE `unifist`.`slug`
  CHANGE `unum` `home` VARCHAR(64) NOT NULL,
  ADD UNIQUE `home_source_model_current` (`home`,`source`,`model`,`current`),
  DROP INDEX `unum_source_model_current`;
