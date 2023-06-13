import { create } from 'zustand';
import { StickyColor } from './style';

interface CreateStickyState {
    createColor: StickyColor | null;
    setCreateColor: (color: StickyColor | null) => void;
}

export const useCreateStickyStore = create<CreateStickyState>()((set) => ({
    createColor: null,
    setCreateColor: (createColor) => set(() => ({ createColor })),
}));
