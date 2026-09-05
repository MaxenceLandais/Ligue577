import DeputeRadarChart from './DeputeRadarChart';

export function FicheDepute({ depute }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-md border border-gray-100">
      <div className="flex items-center gap-4 mb-6">
        <img
          src={depute.photoUrl}
          alt={depute.nom}
          className="w-16 h-16 rounded-full object-cover border"
        />
        <div>
          <h2 className="text-xl font-bold text-gray-900">{depute.nom}</h2>
          <p className="text-sm text-gray-500">{depute.groupe} — {depute.circo}</p>
        </div>
      </div>

      <div className="my-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-2">
          Profil d'orientation économique
        </h3>
        <DeputeRadarChart scores={depute.scores} />
      </div>

      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
        <span className="text-xs font-semibold text-gray-500 uppercase">Synthèse :</span>
        <p className="text-sm text-gray-700 mt-1">
          {depute.synthese_analyse || "Analyse en cours d'évaluation..."}
        </p>
      </div>
    </div>
  );
}