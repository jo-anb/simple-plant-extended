
# Simple Plant

[![Release](https://img.shields.io/github/v/release/jo-anb/simple-plant-extended?style=for-the-badge)](https://github.com/jo-anb/simple-plant-extended/releases/latest)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![Validation](https://github.com/jo-anb/simple-plant-extended/actions/workflows/validate.yml/badge.svg?style=for-the-badge)](https://github.com/jo-anb/simple-plant-extended/actions/workflows/validate.yml)
[![buymeacoffee](https://img.shields.io/badge/buy%20me%20a%20coffee-%23FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/jo-anb)


This is an extention on the [simple-plant](https://github.com/ndesgranges/simple-plant-card) integration from @ndesgranges.
It includes more settings for your plant management. With this integration you can set:
- Fertilization options
- Cleaning options
- Misting options
- Plant ullimination requirements

I also extended the [simple-plant-card](https://github.com/ndesgranges/simple-plant-card) card from @ndesgranges to include these new components in the card.
See the card repo, [simple-plant-extended-card](https://github.com/jo-anb/simple-plant-extended-card)

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jo-anb&repository=simple-plant-extended&category=integration)

OR

1. Install HACS if you don't have it already
2. Open HACS in Home Assistant
3. On the top right side, click the three dot and click `Custom repositories`
4. Where asked for a URL, paste the link of this repository:
https://github.com/jo-anb/simple-plant-extended
5. Where asked for a type, select `integration`
6. Click the download button. ⬇️
7. Install the [simple-plant-extended-card](https://github.com/jo-anb/simple-plant-extended-card) card for your dashboard (optional)

## Entities

This integration provides the following entities

> NOTE: \
> In the following table, `@` represent the name of the device, for example, If I've got a device called "Foo" `test_@` would be `test_foo`

| Entity | Description |
| ------ | ----------- |
| binary_sensor.simple_plant_**todo**_@            | `true` if the plant needs to be watered |
| binary_sensor.simple_plant_{misting/fertilization/cleaning}_**todo**_@            | `true` if the plant needs to be misted, fertilized or cleaned |
| binary_sensor.simple_plant_**problem**_@         | `true` (and labelled as problem) if the plant "water date" is overdue |
| binary_sensor.simple_plant_{misting/fertilization/cleaning}_**problem**_@         | `true` (and labelled as problem) if the plant "misting-
, fertilization- or cleaning date" is overdue |
| button.simple_plant_**mark_{watered,misted/fertilized/cleaned}**_@           | Mark the plant as watered, misted, fertilized or cleaned  |
| date.simple_plant_**last_{watered,misted/fertilized/cleaned}**_@             | Last time the plant has been marked as watered, misted, fertilized or cleaned. In Theory it should not need to be changed manually, but it's there for flexibility |
| date.simple_plant_**next_{watering,misting/fertilization/cleaning}**_@             | Calculated date. Next time the plant has to be watered, misted, fertilized or cleaned. |
| image.simple_plant_**picture**_@                 | Just a picture of your plant to show in your dashboard |
| number.simple_plant_**days_between_{waterings,mistings/fertilizations/cleanings}**_@ | Amount of days to wait before each waterings, mistings, fertilizations or cleanings cycle notification. |
| select.simple_plant_**health**_@                 | A manual dumb selector just to note the current health of your plant, it doesn't do anything else |
| sensor.simple_plant_**next_{watering,misting/fertilization/cleaning}**_@          | Stores the next date a watering, misting, fertilization or cleaning is expected |
|select.simple_plant_illumination_@ | Devince the plants illumination needs, options Sunny, Partly Sunny, Shade|
|select.simple_plant_{misting/cleaning}_enabled_@ | If the plant requeries these options. If true the todo, problem and date sensors will be updated to monitor the schedules according to the days between settings.|
| select.simple_plant_feed_method_@ | What type of fertilization is used for the plant. Options are: Liquid, Sticks or Pebbles

## Credits


This project has been started using [simple-plant](https://github.com/ndesgranges/simple-plant) as a base integration
