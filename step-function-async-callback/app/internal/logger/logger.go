package logger

import (
	"go.uber.org/zap"
)

var sugaredLogger *zap.SugaredLogger

func Init() {
	logger, _ := zap.NewProduction()
	defer logger.Sync() // flushes buffer, if any
	sugaredLogger = logger.Sugar()
}

func Infof(message string, args ...interface{}) {
	sugaredLogger.Infof(message, args)
}

func Debugf(message string, args ...interface{}) {
	sugaredLogger.Debug(message, args)
}

func Errorf(message string, args ...interface{}) {
	sugaredLogger.Error(message, args)
}
