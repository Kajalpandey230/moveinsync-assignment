/**
 * Error handling utility
 * Converts various error formats to displayable strings
 */

export const formatError = (error: any): string => {
  // If it's already a string, return it
  if (typeof error === 'string') {
    return error;
  }

  // If it's an Error object, return its message
  if (error instanceof Error) {
    return error.message;
  }

  // Check for FastAPI validation error format
  const errorDetail = error?.response?.data?.detail || error?.detail || error?.message;

  if (!errorDetail) {
    return 'An unexpected error occurred';
  }

  // Handle array of validation errors (FastAPI format)
  if (Array.isArray(errorDetail)) {
    return errorDetail
      .map((e: any) => {
        if (typeof e === 'string') return e;
        if (e?.msg) return e.msg;
        return JSON.stringify(e);
      })
      .join(', ');
  }

  // Handle string error
  if (typeof errorDetail === 'string') {
    return errorDetail;
  }

  // Handle object error - convert to string
  return JSON.stringify(errorDetail);
};

