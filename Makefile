TRACK_DIR := track_2a

.DEFAULT_GOAL := help

.PHONY: help setup lint run run-mock run-local full splits clean

# Forward all project commands to the Track 2A Makefile. Command-line
# variables such as DATA, IMAGE, and PREDICTIONS are passed through by make.
help setup lint run run-mock run-local full splits clean:
	$(MAKE) -C $(TRACK_DIR) $@