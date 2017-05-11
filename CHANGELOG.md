## 0.6.0
2017-05-11

* Fix bugs with cadence UI not using UTC.
* Fix bug that was caused by target names being strictly numerical.
* Add confirmation dialog to panels on the compose page before removal.
* Text updates and corrections.
* Added Google Analytics and improved logging
* Improvements to admin proposal view (/proposals/semester/2017AB) etc.
* Improve/fix some unit tests
* Add an ordering filter to the homepage. Ability to order by title, created time, updated time, last window.
* Added a target name filter to the front page.
* Minor CSS improvements for a more consistent appearance.

## 0.5.0
2017-05-05

* Fix milliseconds to 0 for telescope availability
* Fix wrong paramter name in telescope availability
* capitalize Observing Budget Explanation
* capitalize Observing Budget Explanation
* Added more specific language about what proposals should and should not be submitted through the portal
* CHange help text for proper motions
* fix typo
* changes to defocus, guiding help text
* change Airmass help text
* Modify acquire mode/radius help text

## 0.4.2
2017-05-01

* Fix for removal of default floyds slit

## 0.4.1
2017-05-01

* Reformat Help page
* Make group id appear as Title in error messages
* Fix bug preventing call to action from showing up on homepage


## 0.4.0
2017-04-28

* Use more consistent validation messages for fields that are required
* Rename help on compose page to How to use this page
* Fix pdf rendering for non firefox browsers
* Remove moon phase from ddt proposal views
* Dont ask user to submit a proposal if they actually do have proposals
* Make sure users can always view their data when viewing a request in the archive by setting the start date to 2014
* Make planning tools link to planning tools on lco.global
* Correct behaviour of minor planet vs comet target composition. Make sure that 0 values in target helper do no validate as false
* Remove STANDARD from molecules that should be counted for acquire duration. Add acquire duration for every spectrum in the request
* Indicate simple interface by header logo
* hide proposal memebers from education users
* In compose form, use proposal titles instead of ids
* Hide even more stuff in simple interface
* Notify existing users when they have been added to a proposal
* Add better error messages when a request does not fit in any visible windows
* Made telescope availability chart more readable
* Description of epoch of elements
* Misc typo fixes
* Expanded help text; added internal/external links

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
