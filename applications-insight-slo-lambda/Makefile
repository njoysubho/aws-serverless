.PHONY: build-ApplicationsInsightsSLO clean

APP_NAME := bootstrap
ZIP_FILE := function.zip

# SAM will call this target during `sam build`
build-ApplicationsInsightsSLO:
	GOOS=linux GOARCH=arm64 go build -o $(APP_NAME) main.go
	zip $(ZIP_FILE) $(APP_NAME)
	cp function.zip $(ARTIFACTS_DIR)

