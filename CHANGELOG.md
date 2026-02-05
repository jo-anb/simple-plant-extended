# CHANGELOG

<!-- version list -->

## v1.1.0 (2026-02-05)

### Bug Fixes

- **config**: Add scope selection for configuration to split plant level and integration level
  configs like notifications
  ([`61aecae`](https://github.com/jo-anb/simple-plant-extended/commit/61aecae31f2f3c9d3c7471c7f947c933da1da6e0))

- **notes**: Fix note logging not stored in device state and service for adding notes not working
  ([`127239f`](https://github.com/jo-anb/simple-plant-extended/commit/127239f3776a36c44e2f93eba7dbb2863b5e14a1))

- **state**: Prevent processing of unknown or unavailable states in activity_log
  ([`24a96d3`](https://github.com/jo-anb/simple-plant-extended/commit/24a96d3ebfbd83582428d99859f9541e740eef42))

### Build System

- Add release config
  ([`65cf897`](https://github.com/jo-anb/simple-plant-extended/commit/65cf897b7e8f3d7f05c86793a521421c9b4004b7))

### Chores

- Add .env to gitignore
  ([`787f98f`](https://github.com/jo-anb/simple-plant-extended/commit/787f98f882345178e7ef31baab06c5b86e07104b))

- Setup release workflow
  ([`fca6477`](https://github.com/jo-anb/simple-plant-extended/commit/fca6477846204106758e979d2d1856e4c9697df3))

- Update cp script
  ([`9e35e62`](https://github.com/jo-anb/simple-plant-extended/commit/9e35e6257bce3e9565b1f3459d409e8cf1b94b27))

### Documentation

- Add more badges
  ([`339da37`](https://github.com/jo-anb/simple-plant-extended/commit/339da37f9c49caf47f4a5d2a618a03c651002c38))

- Update url
  ([`e49ca63`](https://github.com/jo-anb/simple-plant-extended/commit/e49ca634a46b279369bc2b98333c842d735524e3))

- Update validate badge style
  ([`7460fe7`](https://github.com/jo-anb/simple-plant-extended/commit/7460fe7de53c43e8c342e3f92ff0a4856d727ae1))

### Features

- **activity-log**: Implement activity logging for plant state changes and note additions
  ([`4dccfae`](https://github.com/jo-anb/simple-plant-extended/commit/4dccfaead02a402257050a783d08b14f58375506))

- **image**: Add state property to return device name as state
  ([`0b5cc0c`](https://github.com/jo-anb/simple-plant-extended/commit/0b5cc0cd3b0eefc30dfb4ccc4ead8b6fd586bd79))

- **integrations**: Add humidiy, light and temprature sensors to your plant to keep track of
  environment conditions
  ([`2592a59`](https://github.com/jo-anb/simple-plant-extended/commit/2592a598b695f2589cffa503a8037cabe457340d))

- **logs**: Add clear_logs service to remove old activity and notes logs
  ([`860f851`](https://github.com/jo-anb/simple-plant-extended/commit/860f851f61796daded481f14a5a09c483470301c))

- **notification**: Add notification manager for runtime notifications and broadcasts
  ([`0c6661e`](https://github.com/jo-anb/simple-plant-extended/commit/0c6661e2d140302148771eb1bfe2f0acd3d8e06e))

- **plant-info**: Add options to add more info to a plant.
  ([`2592a59`](https://github.com/jo-anb/simple-plant-extended/commit/2592a598b695f2589cffa503a8037cabe457340d))

- **service**: Add reload service to reload Simple Plant Extended entries
  ([`9253aee`](https://github.com/jo-anb/simple-plant-extended/commit/9253aee8deef8e26525f486d25d09a538e068051))

- **status**: Add status sensor with task tracking and update translations
  ([`5c37633`](https://github.com/jo-anb/simple-plant-extended/commit/5c376332a7e3f7305b77327fd0e87dd7d8473875))

### Refactoring

- Applied ruff fixes and code cleanup
  ([`ccea6d1`](https://github.com/jo-anb/simple-plant-extended/commit/ccea6d1cdb4a45df55034af9a39edc1a0abc4f29))

- Formatting
  ([`1542401`](https://github.com/jo-anb/simple-plant-extended/commit/154240124a010da54226d934fe0b327c514f6561))


## v1.0.1 (2026-01-18)

### Bug Fixes

- Extend max number for days-between values to 360
  ([`9b1f97b`](https://github.com/jo-anb/simple-plant-extended/commit/9b1f97b5c5c6de44f6b207f660245b282ac829ff))

### Chores

- Add version tracking to pyproject.toml
  ([`0909e2b`](https://github.com/jo-anb/simple-plant-extended/commit/0909e2b077a1a30231910b6ab0ebcc677809a4d7))

- Configure semantic-release
  ([`588d6a6`](https://github.com/jo-anb/simple-plant-extended/commit/588d6a6eeb6fe9182f0ace5b592e11a054184b65))


## v1.0.0 (2026-01-18)

- Initial Release
