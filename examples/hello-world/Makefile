APP_NAME = HelloWorld
CREATOR_ID = HWr1
BUILD_DIR = build/sdk-$(PALMOS_SDK_VERSION)
CC = m68k-palmos-gcc
PILRC = pilrc
BUILD_PRC = build-prc
SDK_INC = $(PALMOS_SDK)/include
PALMOS_SDK_VERSION ?= $(patsubst sdk-%,%,$(notdir $(PALMOS_SDK)))
CFLAGS = -palmos$(PALMOS_SDK_VERSION) -nostdinc -O2 -Wall -I$(SDK_INC) -I$(SDK_INC)/Core -I$(SDK_INC)/Core/UI -I$(SDK_INC)/Core/System -I$(SDK_INC)/Core/Hardware -I$(SDK_INC)/Dynamic -I$(SDK_INC)/Libraries
# SDK 3.1 predates the PalmOS.h umbrella header; Pilot.h is its equivalent.
ifeq ($(wildcard $(SDK_INC)/PalmOS.h),)
CFLAGS += -DPALMDEV_LEGACY_SDK
endif

.PHONY: all clean
all: $(BUILD_DIR)/$(APP_NAME).prc
$(BUILD_DIR)/$(APP_NAME).prc: $(BUILD_DIR)/$(APP_NAME) $(BUILD_DIR)/.resources
	$(BUILD_PRC) -o $@ -t appl -c $(CREATOR_ID) -n "$(APP_NAME)" $(BUILD_DIR)/$(APP_NAME) $(BUILD_DIR)/*.bin
$(BUILD_DIR)/$(APP_NAME): $(BUILD_DIR)/HelloWorld.o
	$(CC) $(CFLAGS) $< -o $@
$(BUILD_DIR)/HelloWorld.o: src/HelloWorld.c Makefile
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD_DIR)/.resources: resources/HelloWorld.rcp
	@mkdir -p $(BUILD_DIR)
	$(PILRC) $< $(BUILD_DIR)
	@touch $@
clean:
	rm -rf build
