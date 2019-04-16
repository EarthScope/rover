# This is legacy documentation assiocated with the incomplete Rover daemon mode. 
# If found, please disreguard this documentation as it is a record for ROVER's developers. 

 #  ## Background mode: ROVER Subscribe
 #  
 #  ROVER subscribe performs a  `rover retrieve` periodically (see `--recheck-period`)
 #  checking for new data in a server's availabilty server based on subscriptions.
 #  
 #  To support this, a background "daemon" must be running.  This can be
 #  started with:
 #  
 #      rover start
 #  
 #  and stopped with:
 #  
 #      rover stop
 #  
 #  While the daemon is running its status can be seen at http://localhost:8000 (if using the default settings).
 #  
 #  The `subscribe` command to request data has the same format as described above for the `retrieve` command.  For example:
 #  
 #      rover subscribe IU_ANMO_3?_* 2016-01-01T00:00:00 2016-01-02T00:00:00
 #  
 #  If configured, an email will be sent to a users upon completion of each subscription run, (`rover start --email ....`).  
 #  
 #  Processing of subscriptions can be triggered instantenously using
 #  
 #      rover trigger N[:M]
 #      
 #  where N is the subscription index.
 #      
 #  To view existing subscriptions information including subscription indices: 
 #  
 #      rover list-subscribe
 #  
 #  Subscriptions can be deleted using:
 #  
 #      rover unsubscribe N[:M]
 #  
