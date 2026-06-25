import {
  validateEmail,
  validatePassword,
  validateName,
  validateLoginForm,
  validateRegisterForm,
  validateForgotPasswordForm,
  getFieldError,
} from "@/utils/validation";

describe("Validation Utilities", () => {
  describe("validateEmail", () => {
    it("validates email formats correctly", () => {
      expect(validateEmail("bernard@example.com")).toBe(true);
      expect(validateEmail("invalid-email")).toBe(false);
    });
  });

  describe("validatePassword", () => {
    it("validates password complexity correctly", () => {
      expect(validatePassword("SecurePass123!")).toBe(true);
      expect(validatePassword("weak")).toBe(false);
    });
  });

  describe("validateName", () => {
    it("validates name length correctly", () => {
      expect(validateName("Bernard")).toBe(true);
      expect(validateName("")).toBe(false);
    });
  });

  describe("validateLoginForm", () => {
    it("Happy Path: returns isValid true for correct inputs", () => {
      const result = validateLoginForm("bernard@example.com", "SecurePass123!");
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it("Error Condition: catches empty fields and invalid emails", () => {
      const result = validateLoginForm("bad-email", "   ");
      expect(result.isValid).toBe(false);
      expect(getFieldError(result.errors, "email")).toBe(
        "Please enter a valid email address",
      );
      expect(getFieldError(result.errors, "password")).toBe(
        "Password is required",
      );
    });
  });

  describe("validateRegisterForm", () => {
    it("Happy Path: returns isValid true for perfect registration data", () => {
      const result = validateRegisterForm(
        "Bernard",
        "bernard@example.com",
        "SecurePass123!",
        "SecurePass123!",
      );
      expect(result.isValid).toBe(true);
    });

    it("Error Condition: catches password mismatches and weak passwords", () => {
      const result = validateRegisterForm(
        "",
        "bernard@example.com",
        "weak",
        "mismatch",
      );
      expect(result.isValid).toBe(false);
      expect(getFieldError(result.errors, "name")).toBe("Name is required");
      expect(getFieldError(result.errors, "password")).toContain(
        "Password must be at least 8 characters",
      );
      expect(getFieldError(result.errors, "confirmPassword")).toBe(
        "Passwords do not match",
      );
    });
  });

  describe("validateForgotPasswordForm", () => {
    it("Happy Path: validates a correct email", () => {
      const result = validateForgotPasswordForm("bernard@example.com");
      expect(result.isValid).toBe(true);
    });

    it("Error Condition: catches missing emails", () => {
      const result = validateForgotPasswordForm("");
      expect(result.isValid).toBe(false);
      expect(getFieldError(result.errors, "email")).toBe(
        "Email address is required",
      );
    });
  });
});
