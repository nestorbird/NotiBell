# NotiBell
#### _Frappe App for Push Notification, WorkFlow Actions and Check-In with GeoFencing along with Face Recognition through mobile app_

NotiBell is a Custom App build over Frappe that enables user to install NotiBell moile app [Play Store](https://play.google.com/store/apps/details?id=com.nb.notibell) and [App Store](https://testflight.apple.com/join/MtvAjKlz)

| Supports Frappe Versions | Depedency |
|-|-|
|v13 | None|
|v14| HRMS |

### Pre-Requsites
- *Workflow* _ONLY_

### How to Install and Setup
```
bench get-app https://github.com/nestorbird/NotiBell.git --branch main
bench --site <site_name> install-app notibell
```

For more detailed information on installation and workflow setup - [Click here](https://wiki.nestorbird.com/wiki/installation-guide-notibell)

### Features
- Sending Push notification to Mobile App
- Action on Entries according to Workflow depending on Role of logged in User.
- Face Recongnition for Check-In with approval
- Geo Fencing for Check-In with approval

## Contributing
- [Issue Guidelines](https://github.com/frappe/erpnext/wiki/Issue-Guidelines)
- [Pull Request Requirements](https://github.com/frappe/erpnext/wiki/Contribution-Guidelines)

## License
[GNU General Public License (v3)]

## Support
For support please visit or click [here](https://wiki.nestorbird.com/wiki/support)
