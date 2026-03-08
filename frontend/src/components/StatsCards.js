import React from 'react';
import { Shield, AlertTriangle, Activity, Database, Eye } from 'lucide-react';

function StatsCards({ stats, systemStatus }) {
  const cards = [
    {
      title: 'Monitored Files',
      value: stats?.monitored_files || 0,
      icon: Eye,
      color: 'bg-primary-500',
      badge: 'Active',
    },
    {
      title: 'Total Events',
      value: stats?.total_events || 0,
      icon: Activity,
      color: 'bg-blue-500',
      trend: '+12%',
      trendUp: true,
    },
    {
      title: 'Suspicious Events',
      value: stats?.suspicious_events || 0,
      icon: AlertTriangle,
      color: 'bg-warning-500',
      trend: '-5%',
      trendUp: false,
    },
    {
      title: 'Active Incidents',
      value: stats?.active_incidents || 0,
      icon: Shield,
      color: stats?.active_incidents > 0 ? 'bg-danger-500' : 'bg-success-500',
      badge: stats?.active_incidents > 0 ? 'Critical' : 'Secure',
    },
    {
      title: 'Decoy Files',
      value: stats?.decoy_files || 0,
      icon: Database,
      color: 'bg-success-500',
      badge: 'Protected',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
      {cards.map((card, index) => (
        <div key={index} className="card hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{card.title}</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{card.value.toLocaleString()}</p>
              {card.trend && (
                <p className={`text-sm mt-2 ${card.trendUp ? 'text-success-600' : 'text-danger-600'}`}>
                  {card.trend} from last hour
                </p>
              )}
              {card.badge && (
                <span className={`badge mt-2 inline-block ${
                  card.badge === 'Critical' ? 'badge-critical' : 
                  card.badge === 'Secure' ? 'badge-success' : 'badge-low'
                }`}>
                  {card.badge}
                </span>
              )}
            </div>
            <div className={`${card.color} p-3 rounded-lg`}>
              <card.icon className="h-8 w-8 text-white" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default StatsCards;
