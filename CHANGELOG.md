## 0.3.0
2017-04-21

* Remove Submit Proposal link from Nav bar, and make it a link on the Manage Proposals page.
* Added additional help text to notifications_enabled on profile form
* Add link to terms of service
* Address user by first/last name in activation email
* Add link to login form from account activated page
* Change order and display of proposals in userrequest list filter
* close datetime picker on userrequest filter when date is chosen
* Show form errors in sidenav on compose page
* open links on compose page in new tabs, improve filter required error message
* remove instruments from ddt proposal
* remove link to rapid response documentation
* remove deadlines from ddt proposals
* Format field names in sidenav
* Add 1meter nres to spectrographs in configdb is_spectrograp
* Show message when target lookup fails on compose page, improve wording for archive lookup
* hide binning and defocus on spectra observations, default guiding to on for spectra observations
* default exposure time to 60 seconds for calibration molecules on compose page
* Add missing epochofel field for non sidereal target
* Increase alert timeout to 10 seconds
* Allow dec input to accept seconds gt 59 and less than 60
* Only show observation type if it is rapid response
* Chage Child Requests to Sub-requests
* Add tooltip to duration on userrequest row
* Add additional wording to automatic calibration generation
* Simple interface
* add new profile settings and forms
* Implement on authored only email notifications
* Remove binning from compose page
* set max value validation on proper_motion_ra/dec, epoch and parallax
* Webkit does not support const. Fix strange caret css problem with webkit.
* Use friendly instrument names in compose form
* Add link to Rapid Response webpage
* Add link to ETC in new tab
* Fix configutation typo
* All caps IPP
* Add text for RR mode
* Add link to airmass limit webpage
* Add to desc of airmass
* Modify Observing Budget text
* Mods to Obs budget explanation, DDT justification
* Help for defocus, guiding
* Modified slit position, angle
* Modify acquire mode
* Expanded Call for Proposals section
* Modified Your Proposals text
* LCO staff and IAC eligible for standard proposals
* Moon Phase
* Change moon selection from Either to Any
* IPP = INtraProposal Priority

## 0.2.0
2017-04-14

* Format fields in request detail page
* Upgrade to django 1.11
* Format floats in request detail properly
* Prevent fields on compose page from losing focus when validation occurs
* Various typos fixed
* Switch contention plot to chart.js
* Header navigation CSS changes
* Make tools link actually point to the tools page
* Make admin page for requests and user requests load much faster
* Add 'duration' field to API output for getting requests
* Add 'location' details to API output for requests only if they are not blank (I.e. site, observatory, telescope info)
* Add semester_contains filter to /api/semesters endpoint to get semester details given a date[time]
* Initial working pressure and contention plots

## 0.1.0
2017-04-07

* Initial internal release
