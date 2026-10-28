ALTER TABLE `unum`.`route`
  CHANGE `unum` `home` VARCHAR(64) NOT NULL DEFAULT '',
  ADD UNIQUE `identifier_model_source_home_role_holder` (`identifier`,`model`,`source`,`home`,`role`,`holder`),
  DROP INDEX `identifier_model_source_unum_role_holder`;

ALTER TABLE `unum`.`scribe`
  CHANGE `unum` `home` VARCHAR(64) NOT NULL DEFAULT '',
  ADD UNIQUE `identifier_model_source_home` (`identifier`,`model`,`source`,`home`),
  DROP INDEX `identifier_model_source_unum`;
