export const navItems = [
  { label: 'Dashboard', to: '/' },
  { label: 'Examens', to: '/examens' },
  { label: 'Studenten', to: '/studenten' },
  { label: 'Beoordelaars', to: '/beoordelaars' },
  { label: 'Opdrachten', to: '/opdrachten' },
  { label: 'Wachtwoord', to: '/wachtwoord' },
]

export const eventTypes = [
  { value: 'practical', label: 'Praktijk', color: '#B4D7F5' },
  { value: 'avo', label: 'AVO', color: '#9B7DC2' },
  { value: 'keuzedeel', label: 'Keuzedeel', color: '#7FBF7F' },
  { value: 'profialdeel', label: 'Profialdeel', color: '#F4D4A8' },
  // reserved: not used yet but kept for future additions
  { value: 'vakantie', label: 'Vakantie', color: '#9B7DC2' },
  { value: 'examenweek', label: 'Examenweek', color: '#E8A3A3' },
]

export const assessorTypeColors = {
  teacher: { bg: '#dbeafe', text: '#1e40af' },
  external: { bg: '#e8dff5', text: '#7c3aed' },
}

export const studentProgramColors = {
  BOL: { bg: '#e0f2fe', text: '#0369a1' },
  BBL: { bg: '#fce7f3', text: '#be185d' },
}

export const examStatusLabels = {
  planned: 'Gepland',
  scheduled: 'Ingepland',
  in_progress: 'Bezig',
  completed: 'Afgerond',
  cancelled: 'Geannuleerd',
}
