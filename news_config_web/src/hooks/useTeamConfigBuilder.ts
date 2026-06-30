import { create } from "zustand";

import {
  CATEGORY_OPTIONS,
  cloneTemplate,
  parseDelimitedInput,
  SUBCATEGORY_OPTIONS,
  TEAM_PRESETS,
  type TeamTemplate,
} from "@/utils/teamTemplates";

type BuilderState = {
  presetKey: string;
  config: TeamTemplate;
  loadPreset: (presetKey: string) => void;
  updateField: (field: keyof TeamTemplate, value: string | boolean | string[]) => void;
  updatePreferenceText: (field: "include_keywords" | "exclude_keywords", value: string) => void;
  updateMaxItems: (value: number) => void;
  toggleCategory: (category: string) => void;
  toggleSubcategory: (subcategory: string) => void;
};

const initialPreset = TEAM_PRESETS[0];

export const useTeamConfigBuilder = create<BuilderState>((set) => ({
  presetKey: initialPreset.key,
  config: cloneTemplate(initialPreset),
  loadPreset: (presetKey) => {
    const nextPreset = TEAM_PRESETS.find((item) => item.key === presetKey) ?? initialPreset;
    set({
      presetKey: nextPreset.key,
      config: cloneTemplate(nextPreset),
    });
  },
  updateField: (field, value) =>
    set((state) => ({
      config: {
        ...state.config,
        [field]: value,
      },
    })),
  updatePreferenceText: (field, value) =>
    set((state) => ({
      config: {
        ...state.config,
        preferences: {
          ...state.config.preferences,
          [field]: parseDelimitedInput(value),
        },
      },
    })),
  updateMaxItems: (value) =>
    set((state) => ({
      config: {
        ...state.config,
        preferences: {
          ...state.config.preferences,
          max_items: Math.max(1, value),
        },
      },
    })),
  toggleCategory: (category) =>
    set((state) => {
      const exists = state.config.preferences.categories.includes(category);
      const categories = exists
        ? state.config.preferences.categories.filter((item) => item !== category)
        : [...state.config.preferences.categories, category];

      const nextCategories = categories.filter((item) => CATEGORY_OPTIONS.includes(item));
      return {
        config: {
          ...state.config,
          preferences: {
            ...state.config.preferences,
            categories: nextCategories,
          },
        },
      };
    }),
  toggleSubcategory: (subcategory) =>
    set((state) => {
      const exists = state.config.preferences.subcategories.includes(subcategory);
      const subcategories = exists
        ? state.config.preferences.subcategories.filter((item) => item !== subcategory)
        : [...state.config.preferences.subcategories, subcategory];

      const nextSubcategories = subcategories.filter((item) => SUBCATEGORY_OPTIONS.includes(item));
      return {
        config: {
          ...state.config,
          preferences: {
            ...state.config.preferences,
            subcategories: nextSubcategories,
          },
        },
      };
    }),
}));
