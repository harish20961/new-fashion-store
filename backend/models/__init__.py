# MongoDB is schema-less, so there are no ORM model classes here.
#
# As the project grows, use this folder for plain-Python "shape" helpers,
# e.g. functions that build a well-formed product/user/order dict before
# it's inserted, or (optionally) simple JSON-schema validators. Keeping
# these separate from routes/ keeps the route files focused on HTTP logic.
