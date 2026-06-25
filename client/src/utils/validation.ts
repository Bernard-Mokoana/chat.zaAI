import type { FormValidationResult, ValidationError } from "@/types/types";

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(email: string): boolean {
  return EMAIL_REGEX.test(email.trim());
}

export function validatePassword(password: string): boolean {
  return password.length >= 8;
}

export function validateName(name: string): boolean {
  const trimmed = name.trim();
  return trimmed.length >= 2 && trimmed.length <= 100;
}
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
      message: "Name must be between 2 and 100 characters",
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
      message: "Password must be at least 8 characters",
    });
  }

  const trimmedConfirmPassword = confirmPassword?.trim();

  if (
    trimmedConfirmPassword !== undefined &&
    trimmedPassword !== trimmedConfirmPassword
  ) {
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

export function getFieldError(
  errors: ValidationError[],
  field: string,
): string | undefined {
  return errors.find((err) => err.field === field)?.message;
}
