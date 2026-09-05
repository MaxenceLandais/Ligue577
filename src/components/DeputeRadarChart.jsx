import React from 'react';
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from 'recharts';

// Correspondance entre les codes de votre data.json et les libellés affichés
const AXES_CONFIG = {
  FIS: { label: 'Fiscalité', fullMark: 100 },
  ETA: { label: 'Emprise de l\'État', fullMark: 100 },
  REG: { label: 'Réglementation', fullMark: 100 },
  PRO: { label: 'Protectionnisme', fullMark: 100 },
  LIB: { label: 'Liberté économique', fullMark: 100 },
  OUV: { label: 'Ouverture marchés', fullMark: 100 }
};

export default function DeputeRadarChart({ scores }) {
  // Formatage des données pour le RadarChart de Recharts
  const chartData = Object.keys(AXES_CONFIG).map((key) => ({
    subject: AXES_CONFIG[key].label,
    score: scores?.[key] ?? 50,
    fullMark: 100,
  }));

  return (
    <div style={{ width: '100%', height: '350px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
          <PolarGrid stroke="#e2e8f0" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: '#334155', fontSize: 12, fontWeight: 500 }}
          />
          <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#cbd5e1" />
          <Radar
            name="Profil libéral"
            dataKey="score"
            stroke="#2563eb"
            fill="#3b82f6"
            fillOpacity={0.4}
          />
          <Tooltip
            formatter={(value) => [`${value} / 100`, 'Score']}
            contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', borderColor: '#cbd5e1' }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}