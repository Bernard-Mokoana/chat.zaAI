import { renderHook, act } from "@testing-library/react";
import { useSessionManagement } from "@/hooks/useSessionManagement";
import * as sessionStorageService from "@/services/storage/sessionStorage";

jest.mock("@/services/storage/sessionStorage", () => ({
  loadSessions: jest.fn(),
  saveSession: jest.fn(),
  deleteSession: jest.fn(),
  getActiveSessionId: jest.fn(),
  setActiveSessionId: jest.fn(),
  createSession: jest.fn(),
}));

describe("useSessionManagement Hook", () => {
  const mockSession1 = {
    id: "session-1",
    title: "Test 1",
    messages: [],
    createdAt: 1,
    updatedAt: 1,
  };
  const mockSession2 = {
    id: "session-2",
    title: "Test 2",
    messages: [],
    createdAt: 2,
    updatedAt: 2,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (sessionStorageService.loadSessions as jest.Mock).mockReturnValue([
      mockSession1,
      mockSession2,
    ]);
    (sessionStorageService.getActiveSessionId as jest.Mock).mockReturnValue(
      "session-1",
    );
  });

  it("Happy Path: loads initial sessions and active ID on mount", () => {
    const { result } = renderHook(() => useSessionManagement());

    expect(result.current.sessions).toHaveLength(2);
    expect(result.current.activeSessionId).toBe("session-1");
    expect(sessionStorageService.loadSessions).toHaveBeenCalledTimes(1);
  });

  it("Happy Path: setActiveSessionId updates state and storage", () => {
    const { result } = renderHook(() => useSessionManagement());

    act(() => {
      result.current.setActiveSessionId("session-2");
    });

    expect(result.current.activeSessionId).toBe("session-2");
    expect(sessionStorageService.setActiveSessionId).toHaveBeenCalledWith(
      "session-2",
    );
  });

  it("Happy Path: saveCurrentSession adds a new session to the top of the list", () => {
    const { result } = renderHook(() => useSessionManagement());
    const newSession = {
      id: "session-3",
      title: "Test 3",
      messages: [],
      createdAt: 3,
      updatedAt: 3,
    };

    act(() => {
      result.current.saveCurrentSession(newSession);
    });

    expect(sessionStorageService.saveSession).toHaveBeenCalledWith(newSession);
    expect(result.current.sessions).toHaveLength(3);
    expect(result.current.sessions[0]).toBe(newSession); // Inserted at the beginning
  });

  it("Happy Path: saveCurrentSession updates an existing session in place", () => {
    const { result } = renderHook(() => useSessionManagement());
    const updatedSession1 = { ...mockSession1, title: "Updated Title" };

    act(() => {
      result.current.saveCurrentSession(updatedSession1);
    });

    expect(result.current.sessions).toHaveLength(2);
    expect(result.current.sessions[0].title).toBe("Updated Title");
  });

  it("Happy Path: deleteCurrentSession removes it from state and clears activeId if it matches", () => {
    const { result } = renderHook(() => useSessionManagement());

    act(() => {
      result.current.deleteCurrentSession("session-1");
    });

    expect(sessionStorageService.deleteSession).toHaveBeenCalledWith(
      "session-1",
    );
    expect(result.current.sessions).toHaveLength(1);
    expect(result.current.activeSessionId).toBeNull();
  });
});
