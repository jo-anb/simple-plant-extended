
# Simple Plant

[![Release](https://img.shields.io/github/v/release/jo-anb/simple-plant-extended?style=for-the-badge)](https://github.com/jo-anb/simple-plant-extended/releases/latest)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![Validation](https://github.com/jo-anb/simple-plant-extended/actions/workflows/validate.yml/badge.svg?style=for-the-badge)](https://github.com/jo-anb/simple-plant-extended/actions/workflows/validate.yml)
[![buymeacoffee](https://img.shields.io/badge/buy%20me%20a%20coffee-%23FFDD00?style=for-the-badge&logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/joannaomie)


This is an extension of the [simple-plant](https://github.com/ndesgranges/simple-plant-card) integration from @ndesgranges.
It includes more settings for your plant management. With this integration you can set:
- Fertilization options
- Cleaning options
- Misting options
- Plant illumination requirements
- Plant details (size, location, soil, distance to window, pot size, species, notes)
- Optional sensors (humidity, temperature, light)
- Activity and notes timeline

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
| binary_sensor.simple_plant_extended_**todo**_@            | `true` if the plant needs to be watered |
| binary_sensor.simple_plant_extended_{misting/fertilization/cleaning}_**todo**_@            | `true` if the plant needs to be misted, fertilized or cleaned |
| binary_sensor.simple_plant_extended_**problem**_@         | `true` (and labelled as problem) if the plant "water date" is overdue |
| binary_sensor.simple_plant_extended_{misting/fertilization/cleaning}_**problem**_@         | `true` (and labelled as problem) if the plant "misting-, fertilization- or cleaning date" is overdue |
| button.simple_plant_extended_**mark_{watered,misted/fertilized/cleaned}**_@           | Mark the plant as watered, misted, fertilized or cleaned  |
| date.simple_plant_extended_**last_{watered,misted/fertilized/cleaned}**_@             | Last time the plant has been marked as watered, misted, fertilized or cleaned. |
| date.simple_plant_extended_**next_{watering,misting/fertilization/cleaning}**_@             | Calculated date. Next time the plant has to be watered, misted, fertilized or cleaned. |
| image.simple_plant_extended_**picture**_@                 | Just a picture of your plant to show in your dashboard |
| number.simple_plant_extended_**days_between_{waterings,mistings/fertilizations/cleanings}**_@ | Amount of days to wait before each cycle notification. |
| number.simple_plant_extended_**distance_to_window**_@ | Distance to window in cm |
| number.simple_plant_extended_**pot_diameter**_@ | Pot diameter in cm |
| select.simple_plant_extended_**health**_@                 | Manual health selector |
| select.simple_plant_extended_**size**_@                   | Plant size |
| select.simple_plant_extended_**location**_@               | Plant location |
| select.simple_plant_extended_**soil_type**_@              | Soil type |
| select.simple_plant_extended_**illumination**_@           | Illumination needs (Sunny, Partly Sunny, Shade) |
| select.simple_plant_extended_{misting/cleaning}_**enabled**_@ | Enable/disable misting or cleaning schedules |
| select.simple_plant_extended_**feed_method**_@            | Fertilization method (Liquid, Sticks or Pebbles) |
| sensor.simple_plant_extended_**next_{watering,misting/fertilization/cleaning}**_@          | Stores the next date a watering, misting, fertilization or cleaning is expected |
| sensor.simple_plant_extended_**current_humidity**_@       | Linked humidity sensor value |
| sensor.simple_plant_extended_**current_temperature**_@    | Linked temperature sensor value |
| sensor.simple_plant_extended_**current_light**_@          | Linked light sensor value |
| sensor.simple_plant_extended_**plant_age_days**_@         | Plant age in days |
| sensor.simple_plant_extended_**status**_@                 | Status sensor with device attributes and logs |
| text.simple_plant_extended_**notes**_@                    | Free-form notes |
| text.simple_plant_extended_**species**_@                  | Plant species |

## Services

| Service | Description |
| ------ | ----------- |
| simple_plant_extended.add_note | Add a note to the plant timeline and logbook |
| simple_plant_extended.reload | Reload all entries or the entry for a given entity |
| simple_plant_extended.clear_logs | Clear activity and notes logs for a given period |
| simple_plant_extended.update_config | Update acquisition date or linked sensors for a plant |

## Status sensor attributes

The status sensor exposes device attributes and logs, including:

- `notes_log`: list of notes with timestamps
- `activity_log`: list of user-triggered actions with timestamps

## Credits


This project has been started using [simple-plant](https://github.com/ndesgranges/simple-plant) as a base integration
