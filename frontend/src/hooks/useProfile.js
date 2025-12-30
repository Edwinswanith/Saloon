import { useState } from 'react';

/**
 * Custom hook to manage profile modal state
 * Use this in any component to show/hide the profile modal
 */
export const useProfile = () => {
  const [showProfile, setShowProfile] = useState(false);

  const openProfile = () => setShowProfile(true);
  const closeProfile = () => setShowProfile(false);

  return {
    showProfile,
    openProfile,
    closeProfile,
  };
};

