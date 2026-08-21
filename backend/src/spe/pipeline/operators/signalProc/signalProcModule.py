from typing import Dict

import numpy as np

from spe.pipeline.operators.base.dataTypes.heatmapD import HeatmapD
from spe.pipeline.operators.base.dataTypes.scatterplotD import ScatterplotD
from spe.pipeline.operators.base.dataTypes.tableD import TableD
from spe.pipeline.operators.signalProc.dataTypes.signal import Signal, SignalType
from spe.pipeline.operators.module import Module
from spe.runtime.monitor.dataDisplayType import DataDisplayType

from scipy import signal

from streamVizzard import StreamVizzard
from utils.utils import tryParseInt


class SignalProcModule(Module):
    def __init__(self):
        super(SignalProcModule, self).__init__("SignalProc")

    def initialize(self):
        if not StreamVizzard.isDockerExecution():
            self.registerOp("spe.pipeline.operators.signalProc.sources.microphone", "Microphone", "Sources/Microphone")

        self.registerOp("spe.pipeline.operators.signalProc.sources.audioFile", "AudioFile", "Sources/AudioFile")
        self.registerOp("spe.pipeline.operators.signalProc.sources.whiteNoise", "WhiteNoise", "Sources/WhiteNoise")

        self.registerOp("spe.pipeline.operators.signalProc.operators.filter.highpass", "Highpass", "Operators/Filter/Highpass")
        self.registerOp("spe.pipeline.operators.signalProc.operators.filter.lowpass", "Lowpass", "Operators/Filter/Lowpass")
        self.registerOp("spe.pipeline.operators.signalProc.operators.filter.bandpass", "Bandpass", "Operators/Filter/Bandpass")
        self.registerOp("spe.pipeline.operators.signalProc.operators.filter.notchFilter", "NotchFilter", "Operators/Filter/NotchFilter")

        self.registerOp("spe.pipeline.operators.signalProc.operators.gain", "Gain", "Operators/Gain")
        self.registerOp("spe.pipeline.operators.signalProc.operators.resample", "Resample", "Operators/Resample")
        self.registerOp("spe.pipeline.operators.signalProc.operators.flattenSignals", "FlattenSignals", "Operators/FlattenSignals")
        self.registerOp("spe.pipeline.operators.signalProc.operators.extractChannels", "ExtractChannels", "Operators/ExtractChannels")
        self.registerOp("spe.pipeline.operators.signalProc.operators.combineChannels", "CombineChannels", "Operators/CombineChannels")

        signalDT = DataDisplayType("SIGNAL", [DataDisplayType.TypeEntry(SignalType())])
        signalDT.registerDisplayMode(0, self.displayTimeSeries)  # TimeSeries
        signalDT.registerDisplayMode(1, self.displayPowerSpectrumWelch)  # PSD
        signalDT.registerDisplayMode(2, self.displaySpectrogram)  # Spectrogram
        signalDT.registerDisplayMode(3, self.displayMeta)  # Meta Data
        self.registerMonitorDataType(signalDT)

    @staticmethod
    def _extractChannelData(sig: Signal, settings: Dict):
        # Must specify a channel, otherwise return first one!

        channel = tryParseInt(settings.get("channel"), None)

        if channel is not None and sig.channels >= channel >= 1:  # Extract specific channel data [idx starting at 1]
            return sig.data[:, (channel - 1)]

        return sig.data[:, 0]  # First channel als fallback

    def displayTimeSeries(self, sig: Signal, settings: Dict):
        channelData = self._extractChannelData(sig, settings)

        return ScatterplotD.fromElements(channelData.tolist(), settings)

    def displayPowerSpectrumWelch(self, sig: Signal, settings: Dict):
        nperseg = min(len(sig.data), 4096)

        displayChannel = self._extractChannelData(sig, settings)  # Reduces load on welch by only calculating one channel to display

        f, Pxx_spec = signal.welch(displayChannel, sig.samplingRate, 'flattop', nperseg=nperseg, noverlap=int(nperseg/2), scaling='spectrum', axis=0)

        return ScatterplotD.fromElements(list(zip(f.tolist(), 10 * np.log10(Pxx_spec).tolist())), settings)

    def displaySpectrogram(self, sig: Signal, settings: Dict):
        displayChannel = self._extractChannelData(sig, settings)

        f, t, Sxx = signal.spectrogram(displayChannel, sig.samplingRate, axis=0)

        return HeatmapD(t.tolist(), f.tolist(), (10 * np.log10(Sxx + 1e-12)).tolist(), settings)

    @staticmethod
    def displayMeta(sig: Signal, settings: Dict):
        return TableD(["Frames", "Channels", "Sampling Rate"], [[len(sig.data), sig.channels, sig.samplingRate]])
