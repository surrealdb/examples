'use client';

import Image from 'next/image';
import React from 'react';
import PoweredBy from '../../public/powered-by-surrealdb.svg';

export function Footer() {
    return (
        <div className="flex gap-16 py-24 max-md:justify-center">
            <Image
                className="max-h-16 w-[auto]"
                src={PoweredBy}
                alt="Powered by SurrealDB"
            />
        </div>
    );
}
