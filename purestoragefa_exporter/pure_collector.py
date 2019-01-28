# pure_collector.py
# import Python modules
import urllib3

# import third party modules
from prometheus_client.core import GaugeMetricFamily

# disable ceritificate warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PurestorageCollector:
    """ Class that instantiate the collector's methods and properties to
    retrieve metrics from Puretorage Flasharray.
    It implements also a 'collect' method to allow Prometheus client REGISTRY
    to work
    Parameters:
        fa: the authenticated API session to the Purestorage Flasharray
    """
    def __init__(self, fa):
        self.fa = fa
        self._name = None

    @property
    def name(self):
        """(Self) -> str
        it returns the FlashArray name if not already retrieved
        """
        if self._name is None:
            self._name = self.fa.get()['array_name']
        return self._name

    def array_hw(self):
        """(Self) -> iter
        it creates metrics for: temperature, power and components status of
        gauge type with array name and the hw component name as labels.
        Metrics values can be iterated over.
        """
        temp = GaugeMetricFamily('array_temperature', 'Hardware components'
                                 'temperature', labels=['array', 'hw'])
        power = GaugeMetricFamily('array_power', 'Hardware components Power'
                                  'consumption', labels=['array', 'hw'])
        status = GaugeMetricFamily('array_hw_status', 'Hardware'
                                   'components status', labels=['array', 'hw'])
        fa_hw = self.fa.list_hardware()
        for i in fa_hw:
            metric = i['name'].replace('.', '_')
            state = i['status']
            if 'TMP' in metric and i['temperature']:
                temp.add_metric([self.name, metric], i['temperature'])
            if 'PWR' in metric and i['voltage']:
                power.add_metric([self.name, metric], i['voltage'])
            if state == 'ok' or state == 'not_installed':
                status.add_metric([self.name, metric], 1)
            else:
                status.add_metric([self.name, metric], 0)
        yield temp
        yield power
        yield status

    def array_events(self):
        """(Self) -> iter
        it creates a metric for the number open alerts: critical, warning and
        info of gauge type with array name and the severity as labels.
        Metrics values can be iterated over.
        """
        events = GaugeMetricFamily('purestorage_events_total', 'Number of open'
                                   'events', labels=['array', 'severity'])
        fa_events = self.fa.list_messages(open=True)
        ccounter = 0
        wcounter = 0
        icounter = 0
        if len(fa_events) > 0:
            for msg in fa_events:
                severity = msg['current_severity']
                if severity == 'critical':
                    ccounter += 1
                if severity == 'warning':
                    wcounter += 1
                if severity == 'info':
                    icounter += 1
        events.add_metric([self.name, 'critical'], ccounter)
        events.add_metric([self.name, 'warning'], wcounter)
        events.add_metric([self.name, 'info'], icounter)
        yield events

    def array_space(self):
        """(Self) -> iter
        It dinamically creates array space metrics of type gauge with array
        name as a label, metrics are crated only if integer or float value
        returned. Metrics values can be iterated over.
        """
        fa_space = self.fa._request('GET', 'array?space=true')
        for m, v in fa_space[0].items():
            if isinstance(v, (int, float)):
                array_space = GaugeMetricFamily(f'purestorage_array_space_{m}',
                                                'Overall space consumption for'
                                                'Flasharray', labels=['array'])
                array_space.add_metric([self.name], v)
                yield array_space

    def array_perf(self):
        """(Self) -> iter
        It dinamically creates array perf metrics of type gauge with array
        name as a label, metrics are crated only if integer or float value
        returned. Metrics values can be iterated over.
        """
        fa_perf = self.fa._request('GET', 'array?action=monitor')
        for m, v in fa_perf[0].items():
            if isinstance(v, (int, float)):
                array_perf = GaugeMetricFamily(f'purestorage_array_perf_{m}',
                                               'Overall performance metric for'
                                               'Flasharray', labels=['array'])
                array_perf.add_metric([self.name], v)
                yield array_perf

    def vol_space(self):
        """(Self) -> iter
        It dinamically creates volume space metrics of type gauge with array
        and volume name as a labels, metrics are crated only if integer or
        float value returned. Metrics values can be iterated over.
        """
        v_space = self.fa._request('GET', 'volume?space=true')
        # first iterate over metric, value to avoid duplicate metrics
        for m, v in v_space[0].items():
            if isinstance(v, (int, float)):
                vol_space = GaugeMetricFamily(f'purestorage_vol_space_{m}',
                                              'Vol space for Flasharray',
                                              labels=['array', 'volume'])
                # second iterate over volume dicts to populate the metric
                for volume in v_space:
                    vol_name = volume['name'].replace('.', '_')
                    vol_space.add_metric([self.name, vol_name], v)
                yield vol_space

    def vol_perf(self):
        """(Self) -> iter
        It dinamically creates volume space metrics of type gauge with array
        and volume name as a labels, metrics are crated only if integer or
        float value returned. Metrics values can be iterated over.
        """
        v_perf = self.fa._request('GET', 'volume?action=monitor')
        # first iterate over metric, value to avoid duplicate metrics
        for m, v in v_perf[0].items():
            if isinstance(v, (int, float)):
                vol_perf = GaugeMetricFamily(f'purestorage_vol_perf_{m}',
                                              'Vol perf for Flasharray',
                                              labels=['array', 'volume'])
                # second iterate over volume dicts to populate the metric
                for volume in v_perf:
                    vol_name = volume['name'].replace('.', '_')
                    vol_perf.add_metric([self.name, vol_name], v)
                yield vol_perf

    def collect(self):
        """(Self) -> iter
        Aggregates the collection of the Purestorage Flasharray colelctor
        metrics under the collect method for Prometheus client REGISTRY
        """
        yield from self.array_hw()
        yield from self.array_events()
        yield from self.array_space()
        yield from self.array_perf()
        yield from self.vol_space()
        yield from self.vol_perf()
