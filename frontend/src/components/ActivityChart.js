import React from 'react';
import { Activity } from 'lucide-react';

function ActivityChart({ events }) {
  // Group events by hour for the last 24 hours
  const getChartData = () => {
    if (!events || events.length === 0) return [];

    const hourlyData = {};
    const now = new Date();

    // Initialize last 12 hours
    for (let i = 11; i >= 0; i--) {
      const hour = new Date(now - i * 3600000);
      const key = hour.getHours();
      hourlyData[key] = { hour: key, total: 0, suspicious: 0 };
    }

    // Count events
    events.forEach(event => {
      const eventDate = new Date(event.timestamp);
      const hour = eventDate.getHours();
      if (hourlyData[hour]) {
        hourlyData[hour].total++;
        if (event.suspicious) {
          hourlyData[hour].suspicious++;
        }
      }
    });

    return Object.values(hourlyData);
  };

  const chartData = getChartData();
  const maxValue = Math.max(...chartData.map(d => d.total), 10);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Activity Overview</h3>
          <p className="text-sm text-gray-600 mt-1">Last 12 hours</p>
        </div>
        <Activity className="h-5 w-5 text-gray-400" />
      </div>

      <div className="h-64">
        {chartData.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-400">
            <p>No activity data</p>
          </div>
        ) : (
          <div className="h-full flex items-end justify-between space-x-2">
            {chartData.map((data, index) => {
              const totalHeight = (data.total / maxValue) * 100;
              const suspiciousHeight = (data.suspicious / maxValue) * 100;

              return (
                <div key={index} className="flex-1 flex flex-col items-center group">
                  <div className="w-full flex flex-col items-center justify-end" style={{ height: '200px' }}>
                    {/* Suspicious events bar */}
                    {data.suspicious > 0 && (
                      <div
                        className="w-full bg-danger-500 rounded-t transition-all group-hover:bg-danger-600"
                        style={{ height: `${suspiciousHeight}%` }}
                        title={`${data.suspicious} suspicious`}
                      />
                    )}
                    {/* Normal events bar */}
                    {data.total - data.suspicious > 0 && (
                      <div
                        className={`w-full bg-primary-500 ${data.suspicious === 0 ? 'rounded-t' : ''} transition-all group-hover:bg-primary-600`}
                        style={{ height: `${totalHeight - suspiciousHeight}%` }}
                        title={`${data.total - data.suspicious} normal`}
                      />
                    )}
                  </div>
                  <div className="mt-2 text-xs text-gray-600 font-medium">
                    {data.hour}:00
                  </div>
                  {/* Tooltip */}
                  <div className="hidden group-hover:block absolute bg-gray-900 text-white text-xs rounded py-1 px-2 -mt-8">
                    Total: {data.total}
                    {data.suspicious > 0 && ` (${data.suspicious} suspicious)`}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="mt-4 flex items-center justify-center space-x-6 text-sm">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-primary-500 rounded"></div>
          <span className="text-gray-600">Normal Events</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-danger-500 rounded"></div>
          <span className="text-gray-600">Suspicious Events</span>
        </div>
      </div>
    </div>
  );
}

export default ActivityChart;
