#!/bin/sh

GLASGOW=$(which glasgow)
#GLASGOW="~/.local/bin/glasgow"
#GLASGOW="/root/.local/bin/glasgow"

sudo $GLASGOW voltage AB 0
sleep 1.5
sudo $GLASGOW voltage AB 3.3; sleep 1 && sudo $GLASGOW run memory-mmc -V A=3.3,B=3.3 --clk B0 --cmd B1 --dat0 B3 --dat1 B4 --dat2 B5 --dat3 B6 info
