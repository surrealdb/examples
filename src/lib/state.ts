import { Sticky } from '@/app/api/sticky/lib';
import { create } from 'zustand';

type StickyColor = Sticky['color'];

interface CreateStickyState {
    createColor: StickyColor | null;
    setCreateColor: (color: StickyColor | null) => void;
}

export const useCreateStickyStore = create<CreateStickyState>()((set) => ({
    createColor: null,
    setCreateColor: (createColor) => set(() => ({ createColor })),
}));
