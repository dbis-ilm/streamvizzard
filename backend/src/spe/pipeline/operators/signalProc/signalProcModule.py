from spe.pipeline.operators.base.dataTypes.scatterplotD import ScatterplotD
from spe.common.dataType import DataType
from spe.pipeline.operators.signalProc.dataTypes.signal import Signal, SignalType
from spe.pipeline.operators.module import Module, MonitorDataType

from scipy import signal

from streamVizzard import StreamVizzard


class SignalProcModule(Module):
    def __init__(self):
        super(SignalProcModule, self).__init__("SignalProc")

    def initialize(self):
        if not StreamVizzard.isDockerExecution():
            self.registerOp("spe.pipeline.operators.signalProc.sources.microphone", "Microphone", "Sources/Microphone")

        self.registerOp("spe.pipeline.operators.signalProc.sources.audioFile", "AudioFile", "Sources/AudioFile")

        self.registerOp("spe.pipeline.operators.signalProc.operators.highpass", "Highpass", "Operators/Highpass")
        self.registerOp("spe.pipeline.operators.signalProc.operators.lowpass", "Lowpass", "Operators/Lowpass")
        self.registerOp("spe.pipeline.operators.signalProc.operators.bandpass", "Bandpass", "Operators/Bandpass")
        self.registerOp("spe.pipeline.operators.signalProc.operators.resample", "Resample", "Operators/Resample")

        self.registerOp("spe.pipeline.operators.signalProc.operators.flattenSignals", "FlattenSignals", "Operators/FlattenSignals")

        self.registerOp("spe.pipeline.operators.signalProc.operators.speechRecognition", "SpeechRecognition", "Operators/SpeechRecognition")

        DataType.register(SignalType.SignalDTD())

        signalDT = MonitorDataType("SIGNAL", lambda x: isinstance(x, Signal))
        signalDT.registerDisplayMode(0, self.displayTimeSeries)  # TimeSeries
        signalDT.registerDisplayMode(1, self.displayPowerSpectrumWelch)  # Spectrum
        self.registerMonitorDataType(signalDT)

    @staticmethod
    def displayTimeSeries(sig: Signal, settings):
        return ScatterplotD.fromElements(sig.data)

    @staticmethod
    def displayPowerSpectrumWelch(sig: Signal, settings):
        f, Pxx_spec = signal.welch(sig.data, sig.samplingRate, 'flattop', len(sig.data), scaling='spectrum')

        return ScatterplotD.fromElements(list(zip(f, Pxx_spec)))
