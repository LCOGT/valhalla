## 1.16.15
2018-10-01

* Fix bug preventing creation of new time allocation groups.

## 1.16.14
2018-09-27

* Added ip address logging to the request logger

## 1.16.13
2018-09-19

* Remove time_requested field from users in proposals for efficiency

## 1.16.12
2018-09-04

* Add Script type molecule support

## 1.16.11
* Set the default acceptability threshold for FLOYDS to 100, other instruments remain at 90.

## 1.16.10
2018-08-07

* Remove bulk proposals deletion, add bulk proposal activation
* Validate ag_name
* Add support for Internet Explorer

## 1.16.9
2018-07-12

* Fix a bug in telescope states merging states too permissively

## 1.16.8
2018-07-10

* Fix bug in replacing start times of loaded draft requests

## 1.16.7
2018-07-05

* Fix IPP rounding error on max_allowable_ipp endpoint

## 1.16.6
2018-06-25

* Fix RR timing issues by moving logic server side
* Add an account removal request form

## 1.16.5
2018-06-21

* Change some date stuff to use moment.utc in compose page

## 1.16.4
2018-06-18

* Change RR window start time error message for more clarity
* Change ordering of /blocks/ endpoint back to natural id order

## 1.16.3
2018-06-04

* Fix attribute naming and isdirty filtering

## 1.16.2
2018-05-31

* Re-added restriction on TOO requests to within 6 hours of current time

## 1.16.1
2018-05-30

* Lake compat fixes: date formats and required block fields

## 1.16.0
2018-05-30

* Lake compatibility

## 1.15.2
2018-05-24

* Update celery version to get a celery bug fix

## 1.15.1
2018-05-24

* Allow setting ID of proposal if it is created manually
* Fixed cloning spectroscopic requests
* Add links to new terms of service and privacy policy

## 1.15.0
2018-05-17

* Adjust user quota calculation
* Revert fix/pond_isdirty

## 1.14.5
2018-05-16

* Reverted restrict TOO request until end of semester
* removed showAgMode and just use the type
* fixed some spectra compose page inconsistencies
* set isdirty method to use scheduler pond credentials

## 1.14.4
2018-05-07

* Re-added restriction on TOO request to within 6  hours of current time
* Removed start time input for TOO requests

## 1.14.3
2018-05-3

* Fix broken celery version pinning

## 1.14.2
2018-05-3

* Include babel-polyfill for JS support in very old browsers

## 1.14.1
2018-05-2

* Revert Restrict TOO request end times to within 6 hours of current time

## 1.14.0
2018-05-02

* Use gunicorn for deployment instead of uwsgi

## 1.13.4
2018-05-02

* Restrict TOO request end times to within 6 hours of current time

## 1.13.3
2018-04-25

* Enable gzip compression for non static reponses

## 1.13.2
2018-04-13

* Fix bug where target values clear if lookup fails

## 1.13.1
2018-04-12

* Fix bug where users profile listed instruments that were no longer available

## 1.13.0
2018-04-05

* Add method for science collaboration partners to enter proposals into the portal
directly

## 1.12.3
2018-03-27

* Fix bug causing user's hours requested to be too large
* Upgrade django-registration-redus to 2.2
* Throttle request creation to 2500/day

## 1.12.2
2018-03-26

* Added integration with simbad2k and auto-filling fields for non-sidereal targets

## 1.12.1
2018-03-26

* Order co-I by last name in proposal submissions

## 1.12.0
2018-03-21

* Ensure proper ordering of timerequests in proposal views
* use as_dict instead of DRF serializers for scheduler endpoint, for great speeeeed.

## 1.11.1
2018-03-19

* Use django send_mass_mail intead of bcc list for notifications to work around mail servers that dont
accept blank To: fields

## 1.11.0
2018-03-19

* Misc validation fixes
* Add semester to TimeRequests to enable Key Proposal submissions across semesters

## 1.10.5
2018-03-13

* Fix serialization of email messages for celery

## 1.10.4
2018-03-13

* Use BCC instead of TO for sending notifications

## 1.10.3
2018-02-28

* Add non science field to proposals

## 1.10.2
2018-02-28

* Only show filters for schedulable instruments

## 1.10.1
2018-02-28

* Sciapplication rewrite. Removes many fields to be replaced by a single pdf upload.
* Always return IPP dictionary for get_max_ipp endpoint

## 1.10.0
2018-02-20

* Initial sciapplication rewrite - first stage

## 1.9.15
2018-02-16

* Revert cache availability data

## 1.9.14
2018-02-16

* First name first initial fix for semester detail
* Add title to semester detail page

## 1.9.13
2018-02-16

* Add Semester detail page

## 1.9.12
2018-02-14

* Encode lookup target name to fix issues with special characters

## 1.9.11
2018-02-13

* Do not allow std_time and too_time fields to be left blank

## 1.9.10
2018-02-12

* Change minimum exposure time to 10ms (from 0)

## 1.9.9
2018-02-08

* Improvements to proposal application printed forms

## 1.9.8
2018-02-06

* Make proposal invitation emails case insensitive

## 1.9.7
2018-02-01

* Fix problem in previous commit wherein ARCs and LAMP_FLATs couldn't be submitted with OPTIONAL guiding

## 1.9.6
2018-01-29

* Prevent Spectrograph observations from specifying anything other than ag_mode ON
* This consumes the previous commit

## 1.9.5
2018-01-19

* Prevent NRES observations specifying ag_mode OFF

## 1.9.4
2018-01-05

* Update is_spectrograph check to consider nres-commissioning a spectrograph.

## 1.9.3
2018-01-02

* Add search fields for sciapplications
* Display simple interface status for public proposals
* Optimizations for front page

## 1.9.2
2018-01-02

* Add additional fields to sciapplications for PIs
* Upgrade WeasyPrint and elasticsearch
* Test on travis with node 9

## 1.9.1
2018-01-02

* Upgrade node to 9.x

## 1.9.0
2018-01-02

* Upgrade to django 2.0

## 1.8.1
2017-12-122

* Remove old coi field

## 1.8.0
2017-12-22

* Change SciApps to require more specific coinvestigator information

## 1.7.6
2017-12-19

* Filter on expose obstype for existing archive frames search
* Upgrade js deps
* Change insufficient time allocation error message
* Show duration of request in days if necessary

## 1.7.5
2017-12-18

* Correct ordering of TimeAllocations in proposal detail
* Catch ES connection errors in Telescope Availability

## 1.7.4
2017-12-13

* Fix bug for users with only spectral time not having telescope class in compose page

## 1.7.3
2017-12-12

* Cache UserRequest durations

## 1.7.2
2017-12-06

* Add downtimedb support to airmass plots and rise-set windows in general.

## 1.7.1
2017-12-06

* Add # users to semester detail pages
* Add min requirements to help page
* Use session storage to store archive bearer token so that it expires.

## 1.7.0
2017-12-4

* Merge per user time limits for proposals

## 1.6.3
2017-12-4

* Fix typo in From field for some emails

## 1.6.2
2017-11-30

* Fix bug in new per instrument time allocations and get schedulable requests

## 1.6.1
2017-11-30

* Fix bug that did not allow submission of spectrums through the UI

## 1.6.0
2017-11-30

* Instrument specific time allocations

## 1.5.1
2017-11-30

* Hotfix for allowing submission of requests in future proposals

## 1.5.0
2017-11-27

* Django2 Compatibility
* Bump rise-set version
* Always display target name as a string
* Uprev JS deps
* Rename LCOGT to LCO for sciapplication porting

## 1.4.3
2017-11-14

* Add instrument_name to timeallocation ahead of time for dec 1 accounting change
* Upgrade some JS deps

## 1.4.2
2017-10-31

* Change ES Query for ES upgrade

## 1.4.1
2017-10-30

* Catch MovingViolation errors caused by bad ephemeris

## 1.4
2017-10-30

* Add support for JPL Major Planet targets

## 1.3.19
2017-10-24

* Put in fallback for legacy binning modes to get the default binnings readout overhead

## 1.3.18
2017-10-20

* Upgrade django-filter to 1.1

## 1.3.17
2017-10-17

* Changed configdb to use a local memory cache so it can check the cache more frequently

## 1.3.16
2017-10-13

* Modify is_dirty check to include recently modified requests

## 1.3.15
2017-10-11

* Rename completion_threshold to acceptability_threshold in the Request model

## 1.3.14
2017-10-10

* Add 's' to the seconds display in the request detail page

## 1.3.13
2017-10-10

* Adjust some minimum completable block help text

## 1.3.12
2017-10-10

* Show extra user information when possible on science applications

## 1.3.11
2017-10-09

* Added completion_threshold to compose UI and set default value to 90.0%

## 1.3.10
2017-10-06

* Fix vis.js Timeline tooltips

## 1.3.9
2017-10-05

* Unify pond block statuses and colors with the scheduler visualization

## 1.3.8
2017-10-04

* Compact typography for proposal submissions

## 1.3.7
2017-09-29

* Auto redirect to first request detail if userrequest only contains a single request
* Preserve linebreaks from textfields in proposal submission
* Link to correct getting started guide
* Add legend to visibility plot history on request detail page

## 1.3.6
2017-09-26

* Add NRES to pressure and contention plots

## 1.3.5
2017-09-26

* Add media/ to dockerignore

## 1.3.4
2017-09-22

* Restrict username length on profile update page to 50 characters
* Filter comissionig instruments from available instruments on compose page

## 1.3.3
2017-09-21

* Add softies to ADMINS
* Add support for NRES to user interface

## 1.3.2
2017-09-19

* Fix NRES overheads

## 1.3.1
2017-09-18

* Add API quota to profile API
* Restrict lengths of username, target name to 50 characters

## 1.3
2017-09-12

* Various typo fixes
* Prevent large cadences from overflowing the screen and forcing user to refresh the page
* Uprev python & JS deps
* Properly format fail reason in external BlockSerialize
* Update docker base image to stretch
* Show api quota on profile page
* Use cdn.lco.global for all assets

## 1.2.3
2017-08-25

* Add completion_threshold model field to request.
* Modify update request state with pond blocks code to calculate completion_percent and compare to threshold.

## 1.2.2
2017-08-15

* Add custom 404 page so users being redirected from the scheduler visualization don't get confused.

## 1.2.1
2017-08-07

* Add legend to block history plot
* Fix bug in request serializer that would attempt to order by method attributes

## 1.2
2017-08-04

* Pin rise set
* Revise throttle limits

## 1.1.12
2017-07-27

* Fix problem with setuptools and travis ci
* Dont perform LookUP is target is not Sidereal
* Fix compatibility with latest responses library
* Set max airmass to 2 for simple interface users
* Allow unicode in compose page
* Fix paramter for active proposals in manage proposals link

## 1.1.11
2017-07-24

* Add separate health check endpoint

## 1.1.10
2017-07-24

* Add request logging at a more granular level
* Fix bug in lookUP so only last call is used

## 1.1.9
2017-07-18

* Uprev some dependencies

## 1.1.8
2017-07-18

* Use rp filter for "red"

## 1.1.7
2017-07-17

 * Don't use html in plain text emails
 * Remove use of mutable querydict
 * Add additional users to admin list

## 1.1.6
2017-07-06

* Return target name for satellite targets
* Make molecule priority a read only field
* Allow valhalladev host
* Catch correct ConnectionError
* Validate that molecule type matches instrument

## 1.1.5
2017-06-22

* Submitted a request will automatically set the priority of molecules in ascending order

## 1.1.4
2017-06-20

* Enable color/high res images for proprietary data

## 1.1.3
2017-06-20

* Install libcairo2 from debian stretch as the version in jessie is too old for WeasyPrint

## 1.1.2
2017-06-20

* Increase AccessToken expire time
* Add periodic task to remove expired tokens every 24hrs
* Send notification email when DDT proposal is submitted
* Fix some typos and other erorrs in sciapplication detail template

## 1.1.1
2017-06-19
* Removed any timeout from the cached isDirty_query_time

## 1.1
2017-06-19

* Add default IPP values on timallocation creation
* Make data jpg preview link to larger jpg version of frame
* Add link to color version of jpg for a frame if available
* Show instrument name instead of code in request detail
* Remove public field from semester
* Fix vis.js version as newest version breaks legend

## 1.0.8
2017-06-15

* Return empty block set when pond is unreachable instead of thowing exception
* Inform user when data is in transit when request is in completed state

## 1.0.7
2017-06-13

* Make UWSGI logs match LCO internal logging format
* Fix bug where adding calibration frames did not update request duration
* Add LogEntry admin so we can keep track of who changes what in the admin
* Validate that windows fit within a defined semester

## 1.0.6
2017-06-08

* Fix ADMINS setting to send emails on server errors
* Fix bug where adding a user to a proposal that was already a member caused a crash
* Change profile endpoint to return all proposals for a user
* Upgrade numpy to 1.13
* Fix a bug in downloading data from userrequests that have many requests

## 1.0.5
2017-06-07

* Add socket-timeout uwsgi option in hopes of avoding corrupt reponse to scheduler enpoint

## 1.0.4
2017-06-06

* Show dates in UT on request detail page
* Change logo to link to lco.global
* Add warning if user is throttled when trying to cancel request
* Prefetch related models in userrequest viewset
* add exclude state filter to userequests

## 1.0.3
2017-06-06

* Increased throttle limits
* Made state read only in Request Serializer

## 1.0.2
2017-06-05

* Added processes to uwsgi
* Fix a bug with zero padding and the pond

## 1.0.1
2017-06-05

* Added two additional filters to userrequests for fitlering on sub requests last update time

## 1.0.0
2017-06-02

* Added button to download API view json on compose page.
* Enable pagination of child requests.
* Fix various inconsistencies between documentation and code.
* Improve UserRequest admin pages.
* Hardcode out NRES.
* Provide simple filter names for ed users.
* Fixed bug with old version of firefox on compose page.
* Refactored telescope states endpoint.
* isDirty fixes.

## 0.7.1
2017-05-22

* Add NRES fields

## 0.7.0
2017-05-19

* Show instrument name instead of fail count on request details
* Remove Valhalla from page titles
* Allow input of RA/Dec with spaces instead of colons
* Minor bug fixes on compose page
* Locked dependencies
* Add API throttling
* Cache rise/set calculations on a per request basis
* Accurate Pressure plot. Backend and UI updates. Now with site lines!
* Fixes for scheduler interface
* Enable failed count
* Add confirmation before submitting observation on compose page
* Misc bug fixes for rise/set calculations
* Exposure time no longer defaults to 30 seconds. It is now blank.
* Added extra context to pressure and contention endpoints
* Misc text updates.

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
* Fix wrong parameter name in telescope availability
* capitalize Observing Budget Explanation
* capitalize Observing Budget Explanation
* Added more specific language about what proposals should and should not be submitted through the portal
* Change help text for proper motions
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
* Don't ask user to submit a proposal if they actually do have proposals
* Make sure users can always view their data when viewing a request in the archive by setting the start date to 2014
* Make planning tools link to planning tools on lco.global
* Correct behaviour of minor planet vs comet target composition. Make sure that 0 values in target helper do no validate as false
* Remove STANDARD from molecules that should be counted for acquire duration. Add acquire duration for every spectrum in the request
* Indicate simple interface by header logo
* hide proposal members from education users
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
* Change Child Requests to Sub-requests
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
* Fix configuration typo
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
