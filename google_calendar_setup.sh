#!/bin/bash

CREDFILE="CalendarCredentials.py"
touch $CREDFILE
echo -n "Enter Google Developer Client ID: "
read clientid
echo
echo -n "Enter Google Developer Client secret: "
read clientsecret
echo
echo -n "Enter Google Developer key: "
read developerkey
echo
echo -n "Enter Google Calendar address: "
read calendar

echo "CLIENT_ID='$clientid'" >> $CREDFILE
echo "CLIENT_SECRET='$clientsecret'" >> $CREDFILE
echo "DEVELOPER_KEY='$developerkey'" >> $CREDFILE
echo "CALENDAR='$calendar'" >> $CREDFILE
