[https://docs.google.com/document/d/1D1C7dyNJan_6ssF2cC-16bWXn26TD5BlDQ1MCQu0S6Y/edit](https://docs.google.com/document/d/1D1C7dyNJan_6ssF2cC-16bWXn26TD5BlDQ1MCQu0S6Y/edit)

# Replicated log v.3

## Iteration 3.

20 - 40 points

The current iteration should provide tunable semi-synchronicity for replication with a retry mechanism that should deliver all messages exactly-once in total order.

**Main features (maximum 20 points):**

1. If message delivery fails (due to connection, or internal server error, or secondary is unavailable) the delivery attempts should be repeated - retry

If one of the secondaries is down and w=3, the client should be blocked until the node becomes available. Clients running in parallel shouldn’t be blocked by the blocked one.

If w>1 the client should be blocked until the message will be delivered to all secondaries required by the write concern level. Clients running in parallel shouldn’t be blocked by the blocked one.

All messages that secondaries have missed due to unavailability should be replicated after (re)joining the master

Retries can be implemented with an unlimited number of attempts but, possibly, with some “smart” delays logic

You can specify a timeout for the master in case if there is no response from the secondary

All messages should be present exactly once in the secondary log - deduplication

* To test deduplication you can generate some random internal server error response from the secondary after the message has been added to the log

The order of messages should be the same in all nodes - total order

* If secondary has received messages [msg1, msg2, msg4], it shouldn’t display the message ‘msg4’ until the ‘msg3’ will be received
* To test the total order, you can generate some random internal server error response from the secondaries

**Self-check acceptance test:**
Start M + S1
send (Msg1, W=1) - Ok
send (Msg2, W=2) - Ok
send (Msg3, W=3) - Wait
send (Msg4, W=1) - Ok
Start S2
Check messages on S2 - [Msg1, Msg2, Msg3, Msg4]

**Additional features:**
Heartbeats (+15 points)
You can implement a heartbeat mechanism to check secondaries’ health (status): Healthy -> Suspected -> Unhealthy.
They can help you to make your retries logic smarter.
You should have an API on the master to check the secondaries’ status: GET /health

**Quorum append (+5 points)**
If there is no quorum the master should be switched into read-only mode and shouldn’t accept messages append requests and should return the appropriate message
