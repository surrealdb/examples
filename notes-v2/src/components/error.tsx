import React from 'react';

export const Error = ({ message }: { message?: string }) =>
    message && <p className="mb-1 text-sm text-red-700">{message}</p>;
