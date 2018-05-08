
# Reliability, Repeatability and Idempotence

## Introduction

There are two common approaches to making reliable software systems:
either make the system as robust as possible, capable of handing all
possible errors, or make it easy to run repeatedly until correct.

Rover takes the second approach.  It is designed ao that most errors
affect only a small part of any operation (by, for example, running
each download as a separate process), and for those errors to be
corrected by re-running the program.

To work reliably, then, it most be possible for Rover to run
repeatedly.  In particular, calling `rover retrieve` should not
download and append data that are already present in the store, or
store will expand in size.

This property - being able to repeat a command while preserving the
existing data - is called *idemptence*.  It is critical for reliable,
long-lived systems.

## Rover Is Generally Idempotent

