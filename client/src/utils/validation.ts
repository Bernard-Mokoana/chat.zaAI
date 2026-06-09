import type { FormValidationResult, ValidationError } from "@/types/types";

/**
 * Email validation regex (RFC 5322 simplified)
 */
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Password requirements regex
 * - At least 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one digit
 * - At least one special character
 */
const PASSWORD_REGEX =
  /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;

/**
 * Validates an email address
 */
export function validateEmail(email: string): boolean {
  return EMAIL_REGEX.test(email.trim());
}

/**
 * Validates password strength
 * Requirements:
 * - Minimum 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one digit
 * - At least one special character (@$!%*?&)
 */
export function validatePassword(password: string): boolean {
  return PASSWORD_REGEX.test(password);
}

/**
 * Validates a name (non-empty, reasonable length)
 */
export function validateName(name: string): boolean {
  const trimmed = name.trim();
  return trimmed.length > 0 && trimmed.length <= 100;
}

/**
 * Validates login form data
 */
export function validateLoginForm(
  email: string,
  password: string,
): FormValidationResult {
  const errors: ValidationError[] = [];

  const trimmedEmail = email.trim();
  const trimmedPassword = password.trim();

  if (!trimmedEmail) {
    errors.push({
      field: "email",
      message: "Email address is required",
    });
  } else if (!validateEmail(trimmedEmail)) {
    errors.push({
      field: "email",
      message: "Please enter a valid email address",
    });
  }

  if (!trimmedPassword) {
    errors.push({
      field: "password",
      message: "Password is required",
    });
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Validates registration form data
 */
export function validateRegisterForm(
  name: string,
  email: string,
  password: string,
  confirmPassword?: string,
): FormValidationResult {
  const errors: ValidationError[] = [];

  const trimmedName = name.trim();
  const trimmedEmail = email.trim();
  const trimmedPassword = password.trim();

  if (!trimmedName) {
    errors.push({
      field: "name",
      message: "Name is required",
    });
  } else if (!validateName(trimmedName)) {
    errors.push({
      field: "name",
      message: "Name must be between 1 and 100 characters",
    });
  }

  if (!trimmedEmail) {
    errors.push({
      field: "email",
      message: "Email address is required",
    });
  } else if (!validateEmail(trimmedEmail)) {
    errors.push({
      field: "email",
      message: "Please enter a valid email address",
    });
  }

  if (!trimmedPassword) {
    errors.push({
      field: "password",
      message: "Password is required",
    });
  } else if (!validatePassword(trimmedPassword)) {
    errors.push({
      field: "password",
      message:
        "Password must contain at least 8 characters, including uppercase, lowercase, a number, and a special character (@$!%*?&)",
    });
  }

  if (confirmPassword !== undefined && trimmedPassword !== confirmPassword) {
    errors.push({
      field: "confirmPassword",
      message: "Passwords do not match",
    });
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Validates forgot password form
 */
export function validateForgotPasswordForm(
  email: string,
): FormValidationResult {
  const errors: ValidationError[] = [];

  const trimmedEmail = email.trim();

  if (!trimmedEmail) {
    errors.push({
      field: "email",
      message: "Email address is required",
    });
  } else if (!validateEmail(trimmedEmail)) {
    errors.push({
      field: "email",
      message: "Please enter a valid email address",
    });
  }

  return {
    isValid: errors.length === 0,
    errors,
  };
}

/**
 * Gets the first error for a specific field
 */
export function getFieldError(
  errors: ValidationError[],
  field: string,
): string | undefined {
  return errors.find((err) => err.field === field)?.message;
}
