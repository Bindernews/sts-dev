# StS Modding Tools
This is a collection of Slay the Spire modding tools.
Currently it includes a maven repository for ModTheSpire, BaseMod, and StSLib
which should make it easier to setup dependencies.

The `schemas` directory will contain a set of JSON schema files for
the different localization files, but that's still a WIP.

# Using sts-maven
First, you need to make a `lib/` directory and put `desktop-1.0.jar`
(from the SlayTheSpire game directory) in there. Then you can run
`just mvn-build` and then `just mvn-cli`

Inside the container, run the `sts-maven` command.