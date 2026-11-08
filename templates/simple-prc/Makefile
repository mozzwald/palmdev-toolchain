# Copy this directory into an application and edit the application settings.
APP_NAME = MyApp
CREATOR_ID = MyAp
# PALMOS_SDK is an SDK directory supplied by palm-build (or your environment).
ifndef PALMOS_SDK
$(error Set PALMOS_SDK to an SDK directory, or build through palm-build)
endif
BUILD_DIR = build/sdk-$(PALMOS_SDK_VERSION)
CC = m68k-palmos-gcc
PILRC = pilrc
BUILD_PRC = build-prc
SDK_INC = $(PALMOS_SDK)/include
PALMOS_SDK_VERSION ?= $(patsubst sdk-%,%,$(notdir $(PALMOS_SDK)))
CFLAGS = -palmos$(PALMOS_SDK_VERSION) -nostdinc -O2 -Wall -I$(SDK_INC) -I$(SDK_INC)/Core -I$(SDK_INC)/Core/UI -I$(SDK_INC)/Core/System -I$(SDK_INC)/Dynamic -I$(SDK_INC)/Libraries
ifeq ($(wildcard $(SDK_INC)/PalmOS.h),)
CFLAGS += -DPALMDEV_LEGACY_SDK
endif

.PHONY: all clean
all: $(BUILD_DIR)/$(APP_NAME).prc
$(BUILD_DIR)/$(APP_NAME).prc: $(BUILD_DIR)/$(APP_NAME) $(BUILD_DIR)/.resources
	$(BUILD_PRC) -o $@ -t appl -c $(CREATOR_ID) -n "$(APP_NAME)" $(BUILD_DIR)/$(APP_NAME) $(BUILD_DIR)/*.bin
$(BUILD_DIR)/$(APP_NAME): $(BUILD_DIR)/main.o
	$(CC) $(CFLAGS) $< -o $@
$(BUILD_DIR)/main.o: src/main.c Makefile
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD_DIR)/.resources: resources/app.rcp
	@mkdir -p $(BUILD_DIR)
	$(PILRC) $< $(BUILD_DIR)
	@touch $@
clean:
	rm -rf build
