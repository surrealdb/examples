'use client';

import Image from 'next/image';
import React from 'react';
import PoweredBy from '../../public/powered-by-surrealdb.svg';

export function Footer() {
    return (
        <div className="flex max-md:justify-center gap-16 py-24">
            <Image
                className="max-h-16 w-min"
                src={PoweredBy}
                alt="Powered by SurrealDB"
            />
        </div>
    );
}
