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
bench get-app https://github.com/nestorbird/NotiBell-Frappe.git --branch main
bench --site <site_name> install-app notibell
```

### Features
- Sending Push notification to Mobile App
- Action on Entries according to Workflow depending on Role of logged in User.
- Face Recongnition for Check-In with approval
- Geo Fencing for Check-In with approval
