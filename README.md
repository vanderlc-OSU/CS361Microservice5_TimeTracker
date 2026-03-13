# CS361Microservice_TimeTracker

PURPOSE:
    Acts as a central clock/reset authority for other microservices.
    Other microservices write a request file asking "should I reset?"
    This service responds YES or NO based on the reset interval the
    user configured.
