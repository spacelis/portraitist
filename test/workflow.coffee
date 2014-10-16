casper = (require 'casper').create
casper.test.begin "Home page", 1, (test) ->
  casper.start "http://localhost:8080", ->
    test.assertTitle "GeoExpert Judgment System", "Open the front page."
    test.assert
  casper.run () ->
    test.done()


